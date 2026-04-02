"""
Main file to run application
This file launches the TreeVisualizer application.
When run directly, it creates an instance of TreeVisualizer and starts
the main pygame event loop for the course visualization interface.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from TreeVisualizer import TreeVisualizer

if __name__ == "__main__":
    visualizer = TreeVisualizer()
    visualizer.run_simulation()
