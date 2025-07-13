# The Ultimate CLI Tool (mycli) - v3.0

A modular, extensible, and powerful command-line framework to automate your digital life.

## Installation

1. Clone this repository.
2. Navigate into the project directory.
3. Create and activate a Python virtual environment (recommended).
4. Run the installer:
   ```bash
   pip install -e .
   ```

## One-Time Configuration

`mycli` is powered by a central configuration file. On first run, it will be created at `~/.mycli/config.json`. You must populate this file with your personal paths and API keys.

- **`mycli config edit`**: The easiest way to open the file and add your details.
- You will need to sign up for free API keys from:
  - [OpenWeatherMap](https://openweathermap.org/api) for weather data
  - [NewsAPI.org](https://newsapi.org/) for news headlines
  - [Alpha Vantage](https://www.alphavantage.co/support/#api-key) for stock prices
- For cloud features, you need to provide your AWS credentials and a default S3 bucket name.

## Command Reference

`mycli` is organized into logical groups. For help on any command or group, use `--help`.

### Core Commands
- `mycli config [show|edit]`: Manage the user config file.
- `mycli sysinfo`: Display system information (CPU, Memory, Disk usage).

### `mycli file` - File & Directory Management
- `organize [PATH]`: Sorts files into subdirectories based on file extensions.
- `cleanup --days N [--path PATH] [--dry-run]`: Deletes files older than N days.
- `deduplicate PATH [--dry-run]`: Removes duplicate files based on content hash.
- `bigfiles PATH [--top N]`: Finds the N largest files in a directory.
- `archive FOLDER [--format zip|tar]`: Compresses a folder into an archive.
- `extract ARCHIVE`: Extracts a .zip or .tar.gz archive.

### `mycli dev` - Developer Toolkit
- `init NAME [--type python|web|node]`: Creates boilerplate for new projects.
- `serve [--port PORT]`: Runs a local HTTP server on specified port.
- `cloc PATH`: Counts lines of code, blank lines, and comments by language.
- `find-todos PATH`: Finds all `TODO:` and `FIXME:` comments in code files.
- `git-summary`: Shows a summary of the current Git repo status and recent commits.

### `mycli convert` - Content Conversion
- `img PATH --to FORMAT [--quality Q]`: Converts images to `png`, `jpg`, or `webp`.
- `extract-audio VIDEO [--output AUDIO.mp3]`: Extracts audio track from video files.
- `pdf-merge --output FILE.pdf`: Combines multiple PDFs into one (interactive).
- `qr TEXT --output FILE.png`: Generates a QR code from text.

### `mycli data` - Data Dashboards
- `weather CITY`: Gets the current weather for a city.
- `stock TICKER...`: Fetches current stock prices for one or more tickers.
- `news [--query Q] [--country COUNTRY]`: Retrieves top news headlines.
- `shorten-url URL`: Makes a long URL shorter using TinyURL.

### `mycli cloud` - AWS S3 Integration
- `ls [S3_PATH]`: Lists files in your S3 bucket or specific path.
- `upload LOCAL_FILE [S3_PATH]`: Uploads a file to S3.
- `download S3_PATH [LOCAL_PATH]`: Downloads a file from S3.

### `mycli crypto` - Security & Hashing
- `hash INPUT [--algo sha256|md5]`: Computes hash of a file or string.
- `passwd [--length N]`: Generates a strong, random password.
- `whois DOMAIN`: Performs a WHOIS lookup on a domain.

## Configuration File Structure

The config file (`~/.mycli/config.json`) contains:

```json
{
  "user_profile": {
    "default_downloads_path": "auto",
    "default_project_parent_dir": "auto"
  },
  "api_keys": {
    "weather_api_key": "YOUR_OPENWEATHERMAP_API_KEY",
    "news_api_key": "YOUR_NEWSAPI_ORG_KEY",
    "alpha_vantage_api_key": "YOUR_ALPHA_VANTAGE_KEY"
  },
  "aws_credentials": {
    "aws_access_key_id": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_access_key": "YOUR_AWS_SECRET_KEY",
    "default_s3_bucket": "your-default-bucket-name"
  },
  "organize_map": {
    ".pdf": "Documents",
    ".docx": "Documents",
    ".md": "Documents",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".webp": "Images",
    ".zip": "Archives",
    ".tar.gz": "Archives",
    ".mp4": "Videos",
    ".mov": "Videos",
    ".mp3": "Music",
    ".iso": "OS_Images",
    ".dmg": "OS_Images"
  }
}
```

## Example Usage

```bash
# System information
mycli sysinfo

# Initialize a new Python project
mycli dev init my-project --type python

# Organize Downloads folder
mycli file organize ~/Downloads

# Count lines of code in a project
mycli dev cloc ./my-project

# Generate a secure password
mycli crypto passwd --length 16

# Create a QR code
mycli convert qr "https://example.com" --output qr.png

# Get weather (requires API key)
mycli data weather "San Francisco"

# Find TODO comments in code
mycli dev find-todos ./src

# Hash a file
mycli crypto hash ./important-file.txt

# Start a local web server
mycli dev serve --port 8080
```

## Error Handling

- **Missing API Keys**: Commands requiring API keys will show helpful error messages if keys are not configured.
- **Missing Dependencies**: Individual features will gracefully fail if optional dependencies are missing.
- **File Operations**: All file operations include safety checks and informative error messages.

## API Requirements

To use the data dashboard features, you'll need free API keys from:

1. **OpenWeatherMap** (weather data): https://openweathermap.org/api
2. **NewsAPI.org** (news headlines): https://newsapi.org/
3. **Alpha Vantage** (stock prices): https://www.alphavantage.co/support/#api-key

All services offer generous free tiers suitable for personal use.

## Dependencies

The tool automatically installs these dependencies:

- `click` - CLI framework
- `psutil` - System information
- `requests` - HTTP requests
- `Pillow` - Image processing
- `PyPDF2` - PDF operations
- `boto3` - AWS S3 integration
- `moviepy` - Video processing
- `qrcode` - QR code generation
- `newsapi-python` - News API client
- `alpha_vantage` - Stock data API client
- `python-whois` - Domain WHOIS lookups

## Contributing

This tool is designed to be easily extensible. To add new commands:

1. Add your command function to the appropriate group in `main.py`
2. Follow the existing patterns for error handling and configuration
3. Update this README with documentation for your new command

## License

This project is open source. Feel free to modify and distribute as needed.

---

**mycli v3.0** - Your ultimate command-line automation companion!