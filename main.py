#!/usr/bin/env python3
import argparse
import asyncio
import logging
import re
import sys
from typing import Optional

from wb_downloader import WildberriesDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download video reviews from Wildberries products',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://www.wildberries.ru/catalog/279956072/detail.aspx
  %(prog)s https://www.wildberries.ru/catalog/279956072/detail.aspx --output my_video.mp4
  %(prog)s https://www.wildberries.ru/catalog/279956072/detail.aspx --output videos/product_279956072.mp4

If --output is not specified, the script will create a directory named after the 
product ID (e.g., "279956072") and save the video as "video.mp4" inside it.
        """
    )
    parser.add_argument('url', help='Wildberries product URL')
    parser.add_argument(
        '--output',
        help='Output video file path (default: creates directory named after product ID)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    downloader = WildberriesDownloader(args.url, args.output)

    # Show where the video will be saved
    if args.output is None:
        product_id = downloader.product_id
        if product_id:
            logger.info(f'Video will be saved to: {product_id}/video.mp4')
        else:
            logger.info('Video will be saved to: output_video.mp4')
    else:
        logger.info(f'Video will be saved to: {args.output}')

    try:
        success = asyncio.run(downloader.download())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info('Download interrupted by user')
        sys.exit(1)
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
