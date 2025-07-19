"""
Wildberries video review downloader with improved error handling and optimization.
"""
import argparse
import asyncio
import logging
import re
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

import aiohttp
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_product_id(url: str) -> Optional[str]:
    """Extract product ID from Wildberries URL."""
    # Pattern to match product ID in URLs like /catalog/279956072/detail.aspx
    pattern = r'/catalog/(\d+)/'
    match = re.search(pattern, url)
    return match.group(1) if match else None


def _wait_for_element(
        driver: webdriver.Chrome,
        selector: str,
        timeout: int = 30,
        scroll_step: int = 500
) -> Optional[object]:
    """
    Scroll down the page until element is found or timeout is reached.

    Params:
        :param driver: WebDriver instance
        :param selector: CSS selector to find
        :param timeout: Maximum time to wait in seconds
        :param scroll_step: Pixels to scroll each iteration

    Returns:
        :returns WebElement if found, None otherwise
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                return element
        except NoSuchElementException:
            pass

        # Scroll down
        driver.execute_script(f'window.scrollBy(0, {scroll_step});')
        time.sleep(1)

    return None


def _find_video_source(driver: webdriver.Chrome) -> Optional[str]:
    """Find video source URL from the page."""
    try:
        # Method 1: Look for video element with src attribute
        video_elements = driver.find_elements(By.CSS_SELECTOR, 'video[src]')
        for video in video_elements:
            src = video.get_attribute('src')
            if src and ('index.m3u8' in src or 'hls' in src):
                logger.info(f'Found video source: {src}')
                return src

        # Method 2: Look for video elements with data attributes
        video_elements = driver.find_elements(By.CSS_SELECTOR, "div[src*='m3u8'], video[data-src*='m3u8']")
        for video in video_elements:
            src = video.get_attribute('src') or video.get_attribute("data-src")
            if src and "m3u8" in src:
                logger.info(f'Found video source from data attribute: {src}')
                return src

        # Method 3: Look in JavaScript variables or network requests
        # Execute JavaScript to find video sources
        js_code = """
        var sources = [];
        var videos = document.querySelectorAll('video');
        videos.forEach(function(video) {
            if (video.src) sources.push(video.src);
            if (video.currentSrc) sources.push(video.currentSrc);
        });
        return sources;
        """

        js_sources = driver.execute_script(js_code)
        for src in js_sources:
            if src and ('index.m3u8' in src or "hls" in src):
                logger.info(f'Found video source via JavaScript: {src}')
                return src

        return None

    except Exception as e:
        logger.error(f'Error finding video source: {e}')
        return None


def _extract_video_previews(driver: webdriver.Chrome) -> list[str]:
    """Extract video preview URLs from the page (legacy method for fallback)."""
    try:
        image_elements = driver.find_elements(
            By.CSS_SELECTOR, '.swiper-wrapper > .swiper-slide > img'
        )

        video_preview_urls = [
            el.get_attribute('src')
            for el in image_elements
            if el.get_attribute('src') and 'preview.webp' in el.get_attribute('src')
        ]

        return video_preview_urls

    except Exception as e:
        logger.error(f'Error extracting video previews: {e}')
        return []


def _trigger_video_play(driver: webdriver.Chrome) -> bool:
    """Try to trigger video playback to load the video source."""
    try:
        # Look for video play button or video thumbnail
        play_selectors = [
            '.slide__video-btn',
            '.wb-player__btn',
            '.wb-player__container',
            '.videoThumb',
            '.mix-block__video',
            'button[aria-label*=\'Play\']'
        ]

        for selector in play_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f'Clicking video element: {selector}')
                        driver.execute_script('arguments[0].click();', element)
                        time.sleep(2)  # Wait for video to load
                        return True
            except Exception as e:
                logger.debug(f'Could not click {selector}: {e}')
                continue

        return False

    except Exception as e:
        logger.error(f'Error triggering video play: {e}')
        return False


class WildberriesDownloader:
    """Main downloader class for Wildberries video reviews."""

    def __init__(self, url: str, output_path: Optional[str] = None):
        self.url = url
        self.product_id = extract_product_id(url)

        downloads_path = Path('downloads')
        downloads_path.mkdir(exist_ok=True)

        # Set output path based on product ID if not provided
        if output_path is None:
            if self.product_id:
                self.output_dir = downloads_path / self.product_id
                self.output_dir.mkdir(exist_ok=True)
                self.output_path = self.output_dir / f'{self.product_id}-video.mp4'
            else:
                self.output_path = Path('output_video.mp4')
        else:
            self.output_path = Path(output_path)
            # Create parent directories if they don't exist
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.temp_dir = Path('temp_downloads')
        self.temp_dir.mkdir(exist_ok=True)

    def _validate_url(self) -> bool:
        """Validate that the URL belongs to Wildberries."""
        parsed = urlparse(self.url)
        return 'wildberries.ru' in parsed.netloc

    def _setup_webdriver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with optimized options."""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-web-security')
        options.add_argument('--window-size=1920,1080')
        # Note: headless mode disabled as mentioned in original code

        # Performance optimizations
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        return webdriver.Chrome(options=options)

    @asynccontextmanager
    async def _http_session(self):
        """Async context manager for HTTP session."""
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            yield session

    async def _download_playlist(self, m3u8_url: str) -> tuple[str, list[str]]:
        """Download and parse M3U8 playlist."""
        async with self._http_session() as session:
            try:
                async with session.get(m3u8_url) as response:
                    if response.status != 200:
                        raise Exception(f'HTTP {response.status} when fetching playlist')

                    content = await response.text()

                    # Parse playlist - filter out comments and empty lines
                    lines = content.strip().split('\n')
                    segment_files = [
                        line.strip()
                        for line in lines
                        if line.strip() and not line.startswith('#')
                    ]

                    if not segment_files:
                        raise Exception('No video segments found in playlist')

                    base_url = m3u8_url.rsplit('/', 1)[0] + '/'
                    return base_url, segment_files

            except Exception as e:
                logger.error(f'Error downloading playlist: {e}')
                raise

    async def _download_segment(self, session: aiohttp.ClientSession,
                                segment_url: str) -> bytes:
        """Download a single video segment."""
        try:
            async with session.get(segment_url) as response:
                if response.status != 200:
                    raise Exception(f'HTTP {response.status} for segment {segment_url}')
                return await response.read()
        except Exception as e:
            logger.error(f'Error downloading segment {segment_url}: {e}')
            raise

    async def _download_all_segments(self, base_url: str, segment_files: list[str]) -> bytes:
        """Download all video segments concurrently."""
        async with self._http_session() as session:
            tasks = [
                self._download_segment(session, urljoin(base_url, segment))
                for segment in segment_files
            ]

            logger.info(f'Downloading {len(tasks)} segments...')
            segments_data = await asyncio.gather(*tasks)

            # Combine all segments
            return b''.join(segments_data)

    def _convert_to_mp4(self, ts_path: Path) -> bool:
        """Convert TS file to MP4 using ffmpeg."""
        try:
            cmd = [
                'ffmpeg', '-y', '-i', str(ts_path),
                '-c', 'copy', '-avoid_negative_ts', 'make_zero',
                str(self.output_path)
            ]

            logger.info('Converting TS to MP4...')
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                logger.info(f'Video successfully converted to: {self.output_path}')
                return True
            else:
                logger.error(f'FFmpeg conversion failed: {result.stderr}')
                return False

        except FileNotFoundError:
            logger.error('FFmpeg not found. Please install FFmpeg to convert videos.')
            return False
        except Exception as e:
            logger.error(f'Error during conversion: {e}')
            return False

    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            for file in self.temp_dir.glob('*'):
                file.unlink()
            self.temp_dir.rmdir()
        except Exception as e:
            logger.warning(f'Error cleaning up temp files: {e}')

    async def download(self) -> bool:
        """Main download method."""
        if not self._validate_url():
            logger.error('Invalid URL: must be from wildberries.ru')
            return False

        if not self.product_id:
            logger.warning('Could not extract product ID from URL')

        driver = None
        try:
            # Setup WebDriver
            driver = self._setup_webdriver()
            logger.info(f'Loading page: {self.url}')
            driver.get(self.url)

            # Wait for page to load
            time.sleep(20)

            # Method 1: Try to find video source directly
            logger.info('Looking for video source...')
            video_src = _find_video_source(driver)

            if not video_src:
                # Method 2: Try to trigger video playback
                logger.info('Attempting to trigger video playback...')
                if _trigger_video_play(driver):
                    time.sleep(3)  # Wait for video to load
                    video_src = _find_video_source(driver)

            if not video_src:
                # Method 3: Fallback to old method with preview images
                logger.info('Falling back to preview image method...')

                # Wait for user photos section
                logger.info('Waiting for user photos section...')
                element = _wait_for_element(driver, 'section.user-photos')
                if not element:
                    logger.error('User photos section not found')
                    return False

                # Extract video preview URLs
                video_preview_urls = _extract_video_previews(driver)
                if not video_preview_urls:
                    logger.error('No video reviews found')
                    return False

                logger.info(f'Found {len(video_preview_urls)} video preview(s)')

                # Convert first preview URL to M3U8 playlist URL
                first_preview_url = video_preview_urls[0]
                video_src = first_preview_url.replace('preview.webp', 'index.m3u8')

            if not video_src:
                logger.error('Could not find any video source')
                return False

            logger.info(f'Getting playlist: {video_src}')

            # Download and parse playlist
            base_url, segment_files = await self._download_playlist(video_src)
            logger.info(f'Found {len(segment_files)} video segments')

            # Download all segments
            video_data = await self._download_all_segments(base_url, segment_files)

            # Save temporary TS file
            temp_ts = self.temp_dir / 'temp_video.ts'
            temp_ts.write_bytes(video_data)
            logger.info(f'Saved temporary TS file: {temp_ts}')

            # Convert to MP4
            success = self._convert_to_mp4(temp_ts)

            return success

        except Exception as e:
            logger.error(f'Download failed: {e}')
            return False
        finally:
            if driver:
                driver.quit()
            self._cleanup_temp_files()
