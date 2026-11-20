"""Native bundle entry point; normal service and offline release verification."""
import multiprocessing
import sys

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if '--self-test' in sys.argv:
        from rwstudio.runtime_check import main
    else:
        from rwstudio.service import main
    main()
