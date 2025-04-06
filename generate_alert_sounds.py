from gtts import gTTS
import os
import time

def generate_tts_alerts():
    """Generate and save text-to-speech alert sounds"""
    # Create sounds directory
    os.makedirs("sounds", exist_ok=True)

    # Define alert messages
    alerts = {
        "loitering": "Warning! Loitering detected.",
        "pacing": "Warning! Suspicious pacing behavior detected.",
        "intrusion": "Alert! Intrusion into restricted zone.",
        "high_risk": "High risk behavior detected! Security response required."
    }

    # Generate and save TTS files
    for alert_type, text in alerts.items():
        print(f"Generating {alert_type} alert...")

        # Create the TTS object
        tts = gTTS(text=text, lang='en')

        # Save as MP3
        mp3_path = f"sounds/{alert_type}_alert.mp3"
        tts.save(mp3_path)

    print("All alert sounds generated successfully!")

    # Test if files exist
    for alert_type in alerts.keys():
        wav_path = f"sounds/{alert_type}_alert.wav"
        mp3_path = f"sounds/{alert_type}_alert.mp3"

        if os.path.exists(wav_path):
            print(f"✓ {wav_path} - {os.path.getsize(wav_path)/1024:.1f} KB")
        elif os.path.exists(mp3_path):
            print(f"✓ {mp3_path} - {os.path.getsize(mp3_path)/1024:.1f} KB")
        else:
            print(f"✗ Alert sound for {alert_type} not found!")

def test_play_sound():
    """Test playing the generated sounds"""
    # Try different audio libraries
    sound_file = "sounds/high_risk_alert.wav"
    if not os.path.exists(sound_file):
        sound_file = "sounds/high_risk_alert.mp3"

    if not os.path.exists(sound_file):
        print("No sound files found to test!")
        return

    print(f"Testing playback of {sound_file}...")

    # Method 1: playsound
    try:
        from playsound import playsound
        print("Testing with playsound...")
        playsound(sound_file)
        print("playsound completed")
        time.sleep(1)
    except Exception as e:
        print(f"playsound error: {e}")

    # Method 3: system commands
    print("Testing with system command...")
    if os.name == 'nt':  # Windows
        os.system(f'start {sound_file}')
    elif os.name == 'posix':  # macOS or Linux
        if os.path.exists('/usr/bin/afplay'):  # macOS
            os.system(f'afplay {sound_file}')
        else:  # Linux
            os.system(f'aplay {sound_file}')
    print("System command completed")

if __name__ == "__main__":
    # Generate alert sounds
    generate_tts_alerts()

    # Ask to test playback
    response = input("Would you like to test playing the sounds? (y/n): ")
    if response.lower() in ['y', 'yes']:
        test_play_sound()

    print("Sound generation complete!")