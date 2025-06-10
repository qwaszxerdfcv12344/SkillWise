import os
import sys
import webbrowser
import streamlit.web.cli as stcli

if __name__ == "__main__":
    # When running as a PyInstaller bundle, ensure the correct path
    if getattr(sys, 'frozen', False):
        script_path = os.path.join(sys._MEIPASS, "app.py")
    else:
        script_path = "app.py"
    
    # Run Streamlit on a specific port and open the browser
    port = 8501
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    
    # Run the Streamlit app
    sys.argv = ["streamlit", "run", script_path, "--server.port", str(port)]
    sys.exit(stcli.main())