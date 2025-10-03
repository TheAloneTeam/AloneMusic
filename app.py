import sys
import asyncio

print("🚀 Starting AloneMusic Bot...")

try:
    # Run the package as module
    import runpy

    runpy.run_module("AloneMusic", run_name="__main__")
except Exception as e:
    print("❌ Bot crashed with error:", e)
    sys.exit(1)
