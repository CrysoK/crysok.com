import os
import click
from app.logger import log
from app.config import Config

babel_cfg = Config.BABEL_CLI_CONFIG
i18n_dir = Config.BABEL_CLI_I18N_DIR


def babel_update():
    """Update all languages."""
    log.info("Updating translations")
    if os.system(f"pybabel extract -F {babel_cfg} -k _l -o temp.pot ."):
        raise RuntimeError("extract command failed")
    if os.system(f"pybabel update -i temp.pot -d {i18n_dir}"):
        raise RuntimeError("update command failed")
    os.remove("temp.pot")


def babel_compile():
    """Compile all languages."""
    log.info("Compiling translations")
    if os.system(f"pybabel compile -d {i18n_dir}"):
        raise RuntimeError("compile command failed")


def babel_init(lang):
    """Initialize a new language."""
    log.info("Initializing new language")
    if os.system(f"pybabel extract -F {babel_cfg} -k _l -o temp.pot ."):
        raise RuntimeError("extract command failed")
    if os.system(f"pybabel init -i temp.pot -d {i18n_dir} -l {lang}"):
        raise RuntimeError("init command failed")
    os.remove("temp.pot")


def register(app):
    log.info("Registering CLI commands")

    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    def update():
        """Update all languages."""
        babel_update()

    @translate.command()
    def compile():
        """Compile all languages."""
        babel_compile()

    @translate.command()
    @click.argument("lang")
    def init(lang):
        babel_init(lang)


log.debug("EOF")
