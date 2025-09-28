#!/usr/bin/env python3
"""
Complete startup script for Indian EHV Substation Digital Twin
Handles both backend and frontend startup
"""

import os
import sys
import time
import subprocess
import threading
import signal
import requests
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DigitalTwinSystem:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        logger.info("🔍 Checking system dependencies...")
        
        # Check Python
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ is required")
            return False
        logger.info(f"✅ Python {sys.version}")
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js {result.stdout.strip()}")
            else:
                logger.error("❌ Node.js is not installed")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js is not installed")
            return False
        
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ npm {result.stdout.strip()}")
            else:
                logger.error("❌ npm is not installed")
                return False
        except FileNotFoundError:
            logger.error("❌ npm is not installed")
            return False
        
        return True
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', 
                'fastapi', 'uvicorn', 'websockets', 'pandas', 'numpy',
                'scikit-learn', 'matplotlib', 'opendssdirect', 'pymodbus',
                'requests', 'sqlite3'
            ])
            logger.info("✅ Python dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Python dependencies: {e}")
            return False
    
    def install_frontend_dependencies(self):
        """Install frontend dependencies"""
        logger.info("📦 Installing frontend dependencies...")
        frontend_dir = Path(__file__).parent / "frontend"
        
        if not frontend_dir.exists():
            logger.error("❌ Frontend directory not found")
            return False
        
        try:
            # Change to frontend directory and install
            os.chdir(frontend_dir)
            subprocess.check_call(['npm', 'install'])
            logger.info("✅ Frontend dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install frontend dependencies: {e}")
            return False
        finally:
            # Change back to root directory
            os.chdir(Path(__file__).parent)
    
    def start_backend(self):
        """Start the backend server"""
        logger.info("🚀 Starting backend server...")
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for backend to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get('http://localhost:8000/api/metrics', timeout=1)
                    if response.status_code == 200:
                        logger.info("✅ Backend server started successfully")
                        return True
                except:
                    pass
                time.sleep(1)
            
            logger.error("❌ Backend server failed to start")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend development server"""
        logger.info("🌐 Starting frontend server...")
        frontend_dir = Path(__file__).parent / "frontend"
        
        try:
            # Change to frontend directory
            os.chdir(frontend_dir)
            
            # Start React development server
            self.frontend_process = subprocess.Popen([
                'npm', 'start'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for frontend to start
            for i in range(60):  # Wait up to 60 seconds
                try:
                    response = requests.get('http://localhost:3000', timeout=1)
                    if response.status_code == 200:
                        logger.info("✅ Frontend server started successfully")
                        return True
                except:
                    pass
                time.sleep(1)
            
            logger.error("❌ Frontend server failed to start")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
            return False
        finally:
            # Change back to root directory
            os.chdir(Path(__file__).parent)
    
    def start_system(self):
        """Start the complete system"""
        logger.info("🇮🇳 Starting Indian EHV Substation Digital Twin System")
        logger.info("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False
        
        # Install dependencies
        if not self.install_python_dependencies():
            logger.error("❌ Failed to install Python dependencies")
            return False
        
        if not self.install_frontend_dependencies():
            logger.error("❌ Failed to install frontend dependencies")
            return False
        
        # Start backend
        if not self.start_backend():
            logger.error("❌ Failed to start backend")
            return False
        
        # Start frontend
        if not self.start_frontend():
            logger.error("❌ Failed to start frontend")
            return False
        
        self.running = True
        
        # Print access information
        logger.info("")
        logger.info("🎉 Digital Twin System Started Successfully!")
        logger.info("=" * 60)
        logger.info("🌐 Frontend Dashboard: http://localhost:3000")
        logger.info("🔌 Backend API: http://localhost:8000")
        logger.info("📚 API Documentation: http://localhost:8000/docs")
        logger.info("🔌 WebSocket: ws://localhost:8000/ws")
        logger.info("")
        logger.info("📋 Available Features:")
        logger.info("  • Real-time monitoring dashboard")
        logger.info("  • Asset management and control")
        logger.info("  • SCADA data visualization")
        logger.info("  • AI/ML analytics and predictions")
        logger.info("  • Professional circuit visualizations")
        logger.info("")
        logger.info("🛑 Press Ctrl+C to stop the system")
        
        return True
    
    def stop_system(self):
        """Stop the complete system"""
        logger.info("🛑 Stopping Digital Twin System...")
        self.running = False
        
        if self.frontend_process:
            logger.info("Stopping frontend server...")
            self.frontend_process.terminate()
            self.frontend_process.wait()
        
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            self.backend_process.wait()
        
        logger.info("✅ System stopped successfully")
    
    def run(self):
        """Run the complete system"""
        try:
            if self.start_system():
                # Keep the system running
                while self.running:
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop_system()

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("Received interrupt signal")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run the system
    system = DigitalTwinSystem()
    system.run()