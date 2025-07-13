#!/usr/bin/env python3
"""
macOS Accessibility Permission Checker

This script checks if the current process has accessibility permissions
required for keyboard monitoring.
"""

import sys
import subprocess
import os

def check_accessibility_permissions():
    """Check if accessibility permissions are granted"""
    print("🔍 Checking macOS Accessibility Permissions...")
    print("=" * 50)
    
    try:
        # Try to import and test keyboard monitoring
        from pynput import keyboard
        
        print("✅ pynput library available")
        
        # Test if we can create a listener (this will fail without permissions)
        def on_press(key):
            return False  # Stop listener immediately
        
        def on_release(key):
            return False
        
        print("🔐 Testing accessibility permissions...")
        
        # Try to create a keyboard listener
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join(timeout=0.1)
        
        print("✅ Accessibility permissions granted!")
        return True
        
    except ImportError:
        print("❌ pynput library not installed")
        print("💡 Install with: pip install pynput")
        return False
        
    except Exception as e:
        print(f"❌ Accessibility permissions denied or error: {e}")
        print("\n🔧 To grant permissions:")
        print("1. Open System Preferences")
        print("2. Go to Security & Privacy → Privacy → Accessibility")
        print("3. Click the lock icon and enter your password")
        print("4. Add the following applications:")
        print("   - Visual Studio Code")
        print("   - Python")
        print("   - Terminal")
        print("5. Restart your terminal/IDE")
        return False

def check_python_path():
    """Check Python executable path"""
    print(f"\n🐍 Python Information:")
    print(f"   Executable: {sys.executable}")
    print(f"   Version: {sys.version}")
    print(f"   Platform: {sys.platform}")

def check_terminal_info():
    """Check terminal information"""
    print(f"\n💻 Terminal Information:")
    print(f"   TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'Unknown')}")
    print(f"   SHELL: {os.environ.get('SHELL', 'Unknown')}")
    print(f"   PWD: {os.getcwd()}")

def main():
    """Main function"""
    print("🚀 macOS Accessibility Permission Checker")
    print("=" * 50)
    
    check_python_path()
    check_terminal_info()
    
    print("\n" + "=" * 50)
    has_permissions = check_accessibility_permissions()
    
    if has_permissions:
        print("\n🎉 Ready for continuous monitoring!")
        print("💡 Run: python src/continuous_monitoring.py")
    else:
        print("\n⚠️  Accessibility permissions required")
        print("💡 Follow the instructions above to grant permissions")
        print("💡 Alternative: Run demo version with: python src/demo_continuous.py")
    
    return has_permissions

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 