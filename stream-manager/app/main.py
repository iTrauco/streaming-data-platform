import streamlit as st
import subprocess
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.stream_manager import StreamManager
from app.database import init_db, get_db
from app.models import Platform

# Initialize session state
if "terminal_output" not in st.session_state:
    st.session_state.terminal_output = []
if "platforms" not in st.session_state:
    st.session_state.platforms = []

# Initialize database
init_db()

# Initialize stream manager
stream_manager = StreamManager()

def add_to_terminal(command: str, output: str):
    """Add command and its output to terminal history"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.terminal_output.append(f"[{timestamp}] $ {command}")
    st.session_state.terminal_output.append(output)
    st.session_state.terminal_output.append("-" * 50)

def setup_stream_commands(platforms):
    """Generate ffmpeg commands for all platforms"""
    commands = []
    for platform in platforms:
        cmd = f"ffmpeg -i rtmp://localhost:1935/live -c copy -f flv {platform.rtmp_url}/{platform.stream_key}"
        commands.append(cmd)
    return commands

def main():
    st.title("Multi-Platform Stream Manager")
    
    # Sidebar for adding platforms
    with st.sidebar:
        st.header("Add New Platform")
        platform_name = st.text_input("Platform Name")
        rtmp_url = st.text_input("RTMP URL")
        stream_key = st.text_input("Stream Key", type="password")
        
        if st.button("Add Platform"):
            db = get_db()
            platform = Platform(
                name=platform_name,
                rtmp_url=rtmp_url,
                stream_key=stream_key
            )
            db.add(platform)
            db.commit()
            st.success(f"Added platform: {platform_name}")
            add_to_terminal(
                f"Adding platform: {platform_name}",
                f"Successfully added platform with RTMP URL: {rtmp_url}"
            )

    # Main content area
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.header("Stream Management")
        db = get_db()
        platforms = db.query(Platform).all()

        # Display configured platforms
        st.subheader("Configured Platforms")
        for platform in platforms:
            st.text(f"• {platform.name}")
            platform_col1, platform_col2 = st.columns(2)
            
            # Add individual platform controls if needed
            with platform_col1:
                if st.button(f"Delete {platform.name}", key=f"delete_{platform.id}"):
                    db.delete(platform)
                    db.commit()
                    st.rerun()

        # Single SSH connection for all platforms
        if st.button("Connect and Setup Streams"):
            command = stream_manager.get_ssh_command()
            add_to_terminal(command, "Establishing SSH connection...")
            
            try:
                # First establish SSH connection
                process = subprocess.Popen(
                    command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Monitor SSH connection
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        add_to_terminal("", output.strip())

                # Once connected, set up streaming commands
                stream_commands = setup_stream_commands(platforms)
                for cmd in stream_commands:
                    add_to_terminal(
                        cmd,
                        "Setting up stream relay..."
                    )
                    try:
                        stream_process = subprocess.Popen(
                            cmd.split(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        # Monitor stream setup
                        while True:
                            output = stream_process.stdout.readline()
                            if output == "" and stream_process.poll() is not None:
                                break
                            if output:
                                add_to_terminal("", output.strip())
                    except Exception as e:
                        st.error(f"Streaming failed: {str(e)}")
                        add_to_terminal("", f"Error: {str(e)}")

                st.success("Successfully connected and set up streams")
                
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
                add_to_terminal("", f"Error: {str(e)}")

        # Optional: Add stop all streams button
        if st.button("Stop All Streams"):
            try:
                # Kill all ffmpeg processes
                kill_cmd = "pkill ffmpeg"
                process = subprocess.run(
                    kill_cmd.split(),
                    capture_output=True,
                    text=True
                )
                add_to_terminal(kill_cmd, "Stopping all streams...")
                st.success("All streams stopped")
            except Exception as e:
                st.error(f"Failed to stop streams: {str(e)}")
                add_to_terminal("", f"Error: {str(e)}")

    # Terminal output in right column
    with col2:
        st.header("Terminal Output")
        terminal_container = st.container()
        
        with terminal_container:
            terminal_text = "\n".join(st.session_state.terminal_output)
            st.text_area(
                label="Terminal Output",
                value=terminal_text,
                height=400,
                key="terminal",
            )

        # Add clear terminal button
        if st.button("Clear Terminal"):
            st.session_state.terminal_output = []
            st.rerun()

if __name__ == "__main__":
    main()