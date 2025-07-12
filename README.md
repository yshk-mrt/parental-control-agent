# Parental Control Agent - Keylogger

This project is a Python script that monitors and records keyboard input.

## Features

- Real-time keystroke monitoring
- Timestamped logging to file
- Color-coded console output
- Exit with ESC key

## Required Dependencies

```bash
pip install pynput rich
```

## macOS Permission Setup

To run this script, you need to configure the following permissions:

### 1. Input Monitoring

1. **System Settings** → **Privacy & Security** → **Input Monitoring**
2. Click the **+** button
3. Add **Terminal** or **Python executable**
4. Enable the checkbox

### 2. Accessibility

1. **System Settings** → **Privacy & Security** → **Accessibility**
2. Tap **Keyboard**
3. Click the **+** button
4. Add **Terminal** or **Python executable**
5. Enable the checkbox

### Important Notes

- **You must completely restart Terminal** after configuring permissions
- Both permissions are required (Input Monitoring AND Accessibility)

## Usage

```bash
python key.py
```

- Once the script starts, keystroke monitoring begins
- Input is displayed in the console and saved to `keystrokes.log`
- Press **ESC key** to exit

## Output Files

- `keystrokes.log`: Timestamped keystroke log

## Disclaimer

- This tool should be used for educational purposes and parental monitoring only
- Unauthorized use on other people's computers may cause legal issues
- Obtain proper permission before use 