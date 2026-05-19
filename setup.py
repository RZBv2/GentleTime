"""
GentleTime ✦ - Setup and installation script
A beautiful productivity timer application with themes, voice announcements, and activity tracking
"""

from setuptools import setup, find_packages
import os
import sys

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "GentleTime ✦ - A beautiful productivity timer application"

# Define requirements
requirements = [
    'pyttsx3>=2.90',
]

# Optional requirements for development
dev_requirements = [
    'pytest>=7.0.0',
    'black>=22.0.0',
    'flake8>=5.0.0',
]

setup(
    name='gentletime',
    version='1.0.0',
    author='GentleTime Contributors',
    author_email='your-email@example.com',
    description='A beautiful productivity timer application with themes and voice announcements',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/username/gentletime',
    project_urls={
        'Bug Reports': 'https://github.com/username/gentletime/issues',
        'Source': 'https://github.com/username/gentletime',
    },
    
    # Package configuration
    py_modules=['gentletime'],
    python_requires='>=3.7',
    
    # Dependencies
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
        'test': ['pytest>=7.0.0'],
    },
    
    # Entry points for command-line execution
    entry_points={
        'console_scripts': [
            'gentletime=gentletime:main',
            'gt=gentletime:main',
        ],
    },
    
    # Metadata
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Office/Business :: Scheduling',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Environment :: X11 Applications',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
    ],
    
    # Keywords for PyPI
    keywords='timer productivity pomodoro focus time-management tkinter voice-assistant',
    
    # License
    license='MIT',
    
    # Platform compatibility
    platforms=['Windows', 'macOS', 'Linux'],
    
    # Include package data
    include_package_data=True,
    zip_safe=False,
)


# Installation helper function
def install_script():
    """Custom installation instructions"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    GentleTime ✦ Installer                     ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Installing GentleTime...
    
    To verify installation, run:
        gentletime
    or
        python -c "import gentletime; print('✓ GentleTime installed successfully')"
    
    For first-time setup:
        1. Run: gentletime
        2. Enter your name when prompted
        3. Start using the timer!
    
    Optional: Install TTS support (recommended):
        pip install pyttsx3
    
    """)

if __name__ == "__main__":
    # Run installation
    setup()
    install_script()