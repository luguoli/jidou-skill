"""Parse SKILL.md YAML metadata safely, without executing YAML constructors."""
from pathlib import Path
import re

try:
    import yaml
except ImportError:
    yaml = None


class SkillFormatError(ValueError):
    """Diagnostics never include source/context values."""


def load_skill(path: Path) -> tuple[dict, str]:
    if yaml is None:
        raise SkillFormatError('YAML support requires PyYAML; install requirements.txt before running the helpers.')
    text = path.read_text(encoding='utf-8')
    match = re.match(r'\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)', text, re.S)
    if not match:
        raise SkillFormatError('SKILL.md needs a YAML frontmatter block delimited by --- lines.')

    class UniqueSafeLoader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            self.flatten_mapping(node)
            result = {}
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                if not isinstance(key, str) or key in result:
                    raise SkillFormatError('YAML metadata has duplicate or non-string mapping keys.')
                result[key] = self.construct_object(value_node, deep=deep)
            return result

    try:
        metadata = yaml.load(match.group(1), Loader=UniqueSafeLoader)
    except yaml.YAMLError:
        raise SkillFormatError('SKILL.md contains invalid YAML metadata.') from None
    if not isinstance(metadata, dict):
        raise SkillFormatError('YAML frontmatter must be a mapping, not a list or scalar.')
    return metadata, text[match.end():]


def skill_version(path: Path) -> str:
    front, _ = load_skill(path)
    metadata = front.get('metadata')
    value = metadata.get('version') if isinstance(metadata, dict) else None
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise SkillFormatError('metadata.version must be a quoted or plain semantic-version string.')
    return value
