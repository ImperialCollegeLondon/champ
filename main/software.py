from django.conf import settings


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


SOFTWARE = [
    clean_software_config(config) for config in settings.PORTAL_CONFIG["software"] or []
]

SOFTWARE_CHOICES = list(enumerate(s["name"] for s in SOFTWARE))
