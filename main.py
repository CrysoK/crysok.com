from werkzeug.serving import is_running_from_reloader
from app import cli, create_app
from app.logger import log

app = create_app()
cli.register(app)

# For local development and debugging purposes
if __name__ == "__main__":
    if not is_running_from_reloader():
        log.info("Updating and compiling translations")
        cli.babel_update()
        cli.babel_compile()
    else:
        log.info("Spawning new process")

    app.run(host="0.0.0.0", port=81, debug=True, load_dotenv=True)


log.debug("EOF")
