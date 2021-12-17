from .portal_config import get_portal_settings


def clean_software_config(config):
    """Take an individual `config` data structure (as specified by
    config_validation.SoftwareSchema) and return a 'clean' version suitable for
    internal use. This allows for a simplified schema to be available to users
    whilst preserving consistent internal data structures by e.g. replacing null
    values with empty lists etc.

    args:
      config (dict): A validated SoftwareSchema

    returns:
      (dict): A cleaned version of `config`
    """

    config = config.copy()
    if not config["input_files"]["required"]:
        config["input_files"]["required"] = []
    if not config["input_files"]["optional"]:
        config["input_files"]["optional"] = []
    return config


def get_software():
    portal_config = get_portal_settings()
    return [clean_software_config(config) for config in portal_config.SOFTWARE or []]


def get_software_choices():
    return list(enumerate(s["name"] for s in get_software()))
