"""Open the browser studio locally. Python standard library only; no pip needed."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0, help='Local port (0 chooses a free port)')
    parser.add_argument('--no-browser', action='store_true', help='Print the URL without opening it')
    args = parser.parse_args()
    web = Path(__file__).resolve().parent / 'web'
    if not (web / 'index.html').is_file():
        parser.error('Missing web/index.html. Extract the complete project ZIP first.')
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535.')
    handler = partial(SimpleHTTPRequestHandler, directory=str(web))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError as error:
        parser.exit(1, f'Could not start the local server: {error}\n')
    with server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'Aegis studio: {url}\nKeep this window open. Press Ctrl+C to quit.', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nAegis server stopped.')


if __name__ == '__main__':
    main()
