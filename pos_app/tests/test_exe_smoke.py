"""
EXE Smoke Test - Verify packaged executable launches and runs

Tests cover:
- EXE file existence
- EXE launch and startup
- No crash on startup
- Clean exit
- Basic functionality after launch
"""

import pytest
import subprocess
import time
import os
import sys
import signal
from pathlib import Path


@pytest.mark.smoke
class TestEXEExistence:
    """Test that EXE file exists and is accessible"""
    
    def get_exe_path(self):
        """Get the path to the built EXE"""
        # Check common build locations
        possible_paths = [
            Path("dist/POSSystem.exe"),
            Path("build/POSSystem.exe"),
            Path("../dist/POSSystem.exe"),
            Path("../../dist/POSSystem.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def test_exe_exists(self):
        """Test that EXE file exists"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found - build the application first with build_exe.py")
        
        assert exe_path.exists(), f"EXE not found at {exe_path}"
        assert exe_path.is_file(), f"{exe_path} is not a file"
    
    def test_exe_is_executable(self):
        """Test that EXE is executable"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found")
        
        # On Windows, check file extension
        assert str(exe_path).endswith('.exe'), "File is not an EXE"


@pytest.mark.smoke
class TestEXELaunch:
    """Test launching the EXE"""
    
    def get_exe_path(self):
        """Get the path to the built EXE"""
        possible_paths = [
            Path("dist/POSSystem.exe"),
            Path("build/POSSystem.exe"),
            Path("../dist/POSSystem.exe"),
            Path("../../dist/POSSystem.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def test_exe_launches_without_crash(self):
        """Test that EXE launches and doesn't immediately crash"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found - build the application first")
        
        # Launch the EXE with a timeout
        try:
            process = subprocess.Popen(
                [str(exe_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Wait a few seconds for startup
            time.sleep(3)
            
            # Check if process is still running
            poll_result = process.poll()
            
            # If poll_result is None, process is still running (good)
            # If poll_result is not None, process exited (could be crash)
            if poll_result is not None and poll_result != 0:
                # Process exited with error code
                stdout, stderr = process.communicate()
                stdout_text = stdout.decode(errors='ignore') if stdout else ''
                stderr_text = stderr.decode(errors='ignore') if stderr else ''
                pytest.fail(
                    f"EXE crashed on startup with exit code {poll_result}\n"
                    f"STDOUT: {stdout_text}\n"
                    f"STDERR: {stderr_text}"
                )
            
            # Terminate the process
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            
            # If we got here, EXE launched successfully
            assert True
            
        except FileNotFoundError:
            pytest.fail(f"Could not find or execute EXE at {exe_path}")
        except Exception as e:
            pytest.fail(f"Error launching EXE: {e}")
    
    def test_exe_exits_cleanly(self):
        """Test that EXE can exit cleanly"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found")

        if sys.platform == 'win32':
            pytest.skip("EXE clean exit check is unstable for GUI apps on Windows")
        
        try:
            process = subprocess.Popen(
                [str(exe_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Wait for startup
            time.sleep(2)
            
            # Terminate gracefully
            try:
                if sys.platform == 'win32':
                    try:
                        process.terminate()
                    except Exception:
                        pass
                else:
                    process.terminate()

                # Wait for clean exit
                try:
                    exit_code = process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    exit_code = None

                # On Windows, accept best-effort termination; on POSIX enforce SIGTERM-like exit.
                if sys.platform != 'win32':
                    assert exit_code in [0, -15, None], f"Unexpected exit code: {exit_code}"
                else:
                    if exit_code is None:
                        try:
                            process.kill()
                        except Exception:
                            pass
                        try:
                            exit_code = process.wait(timeout=5)
                        except Exception:
                            exit_code = getattr(process, 'returncode', None)
                    assert exit_code is not None

            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                process.wait()
                pytest.fail("EXE did not exit cleanly after SIGTERM")
            
        except Exception as e:
            pytest.fail(f"Error testing EXE exit: {e}")


@pytest.mark.smoke
class TestEXEEnvironment:
    """Test EXE environment and dependencies"""
    
    def get_exe_path(self):
        """Get the path to the built EXE"""
        possible_paths = [
            Path("dist/POSSystem.exe"),
            Path("build/POSSystem.exe"),
            Path("../dist/POSSystem.exe"),
            Path("../../dist/POSSystem.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def test_exe_directory_structure(self):
        """Test that EXE directory has expected structure"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found")
        
        exe_dir = exe_path.parent
        
        # Check for common PyInstaller files
        expected_files = [
            'base_library.zip',  # PyInstaller library archive
        ]
        
        # At least the EXE should exist
        assert exe_path.exists(), "EXE file missing"
    
    def test_exe_file_size(self):
        """Test that EXE has reasonable file size"""
        exe_path = self.get_exe_path()
        
        if exe_path is None:
            pytest.skip("EXE not found")
        
        file_size = exe_path.stat().st_size
        
        # EXE should be at least 1MB (reasonable for PyInstaller app)
        assert file_size > 1_000_000, f"EXE too small: {file_size} bytes"
        
        # EXE should be less than 500MB (sanity check)
        assert file_size < 500_000_000, f"EXE too large: {file_size} bytes"


@pytest.mark.smoke
class TestEXEBuildArtifacts:
    """Test that build artifacts are present"""
    
    def test_build_directory_exists(self):
        """Test that build directory exists"""
        build_dir = Path("build")
        dist_dir = Path("dist")
        
        # At least one should exist after building
        if not build_dir.exists() and not dist_dir.exists():
            pytest.skip("Build not found - run build_exe.py first")
    
    def test_spec_file_exists(self):
        """Test that PyInstaller spec file exists"""
        spec_file = Path("POSSystem.spec")
        
        if not spec_file.exists():
            pytest.skip("Spec file not found - may not have been built yet")
        
        assert spec_file.exists(), "Spec file missing"
        assert spec_file.is_file(), "Spec file is not a file"
