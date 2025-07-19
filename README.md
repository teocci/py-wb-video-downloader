# Wildberries Video Downloader

A Python 3.11+ tool for downloading video reviews from Wildberries product pages. This tool automatically extracts and downloads video reviews from product pages, combining video segments and converting them to MP4 format.

## Features

- **Async Downloads**: Concurrent downloading of video segments for faster processing
- **Auto Conversion**: Automatic conversion from TS to MP4 format
- **Detailed Logging**: Comprehensive logging with optional verbose mode
- **Error Handling**: Robust error handling and cleanup
- **Modern Python**: Built for Python 3.11+ with modern type hints and features

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Google Chrome browser
- ChromeDriver (automatically managed by Selenium)
- FFmpeg (for video conversion)

### Installing FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Using winget
winget install ffmpeg
```

**macOS:**
```bash
# Using Homebrew
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/wildberries-video-downloader.git
cd wildberries-video-downloader
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create requirements.txt file:**
```txt
selenium>=4.15.0
aiohttp>=3.8.0
```

## Usage

### Basic Usage

Download the first video review from a Wildberries product page:

```bash
python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx"
```

### Advanced Usage

```bash
# Specify output file
python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx" --output "my_video.mp4"

# Enable verbose logging
python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx" --verbose

# Combine options
python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx" --output "review.mp4" --verbose
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | Wildberries product URL (required) | - |
| `--output` | Output video file path | `output_video.mp4` |
| `--verbose`, `-v` | Enable verbose logging | `False` |

## How It Works

1. **Page Loading**: Opens the Wildberries product page using Selenium WebDriver
2. **Element Detection**: Scrolls down to find the user photos/reviews section
3. **Video Discovery**: Extracts video preview URLs from review thumbnails
4. **Playlist Retrieval**: Converts preview URLs to M3U8 playlist URLs
5. **Segment Download**: Downloads all video segments concurrently using async HTTP requests
6. **File Combination**: Combines all segments into a single TS file
7. **Format Conversion**: Converts TS to MP4 using FFmpeg
8. **Cleanup**: Removes temporary files

## Configuration

The tool uses Chrome WebDriver with the following optimizations:

- **Window Size**: 1920x1080 for optimal element detection
- **Performance**: Disabled unnecessary Chrome features
- **Headless Mode**: Disabled (required for Wildberries compatibility)

## Error Handling

The tool handles various error scenarios:

- **Invalid URLs**: Validates that URLs belong to wildberries.ru
- **Network Issues**: Retries and proper error messages for connection problems
- **Missing Elements**: Graceful handling when video reviews aren't found
- **FFmpeg Errors**: Clear error messages for conversion issues
- **Cleanup**: Automatic cleanup of temporary files even on errors

## Logging

The tool provides structured logging with two levels:

- **INFO** (default): Basic progress information
- **DEBUG** (verbose): Detailed operation logs

Logs include timestamps and are formatted for easy reading.

## File Structure

```
wildberries-video-downloader/
├── wildberries_downloader.py    # Main script
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── temp_downloads/             # Temporary files (auto-created/cleaned)
```

## Examples

### Successful Download
```bash
$ python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx"
2024-01-15 10:30:15 - INFO - Loading page: https://www.wildberries.ru/catalog/123456789/detail.aspx
2024-01-15 10:30:20 - INFO - Waiting for user photos section...
2024-01-15 10:30:25 - INFO - Found 3 video review(s)
2024-01-15 10:30:25 - INFO - Getting playlist: https://video.wildberries.ru/...
2024-01-15 10:30:26 - INFO - Found 12 video segments
2024-01-15 10:30:26 - INFO - Downloading 12 segments...
2024-01-15 10:30:30 - INFO - Saved temporary TS file: temp_downloads/temp_video.ts
2024-01-15 10:30:30 - INFO - Converting TS to MP4...
2024-01-15 10:30:35 - INFO - Video successfully converted to: output_video.mp4
```

### No Video Reviews Found
```bash
$ python wildberries_downloader.py "https://www.wildberries.ru/catalog/123456789/detail.aspx"
2024-01-15 10:30:15 - INFO - Loading page: https://www.wildberries.ru/catalog/123456789/detail.aspx
2024-01-15 10:30:20 - INFO - Waiting for user photos section...
2024-01-15 10:30:25 - ERROR - No video reviews found
```

## Troubleshooting

### Common Issues

**1. ChromeDriver Issues**
- Ensure Chrome browser is installed and up to date
- Selenium automatically manages ChromeDriver, but you can specify a path if needed

**2. FFmpeg Not Found**
```
ERROR - FFmpeg not found. Please install FFmpeg to convert videos.
```
- Install FFmpeg following the installation instructions above
- Ensure FFmpeg is in your system PATH

**3. Page Loading Issues**
- Some product pages may take longer to load
- Try increasing the timeout in the code if needed
- Ensure stable internet connection

**4. No Video Reviews**
- Not all products have video reviews
- Check that the product page actually contains video reviews

### Debug Mode

Use verbose mode to get detailed information about what's happening:

```bash
python wildberries_downloader.py "URL" --verbose
```

## Limitations

- Only downloads the first video review found on the page
- Requires Chrome browser and cannot run in headless mode
- Depends on Wildberries' current HTML structure
- May need updates if Wildberries changes their video delivery system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and personal use only. Please respect Wildberries' terms of service and copyright policies. The authors are not responsible for any misuse of this tool.

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section
2. Enable verbose logging to get more details
3. Create an issue on GitHub with:
   - Error message
   - Product URL (if not sensitive)
   - Your Python version
   - Operating system

---

**Note**: This tool is not affiliated with Wildberries and is an independent project for educational purposes.