import sublime, sublime_plugin
import re

def _get_setting(key, default=None):
  settings = sublime.load_settings("SortHtmlAttr.sublime-settings")
  return settings.get(key, default)

class SortHtmlAttrCommand(sublime_plugin.TextCommand):
  def __init__(self, view):
    super(SortHtmlAttrCommand, self).__init__(view)

    sp_char = " \u0009\u000a\u000c\u000d"
    ctrl_char = "\u0000-\u001f\u007f-\u009f"
    attr_name = "[^{sp_char}{ctrl_char}\"'>/=]".format(sp_char=sp_char, ctrl_char=ctrl_char)
    attr_pattern = "[{sp_char}]+(({attr_name}+)([{sp_char}]*=[{sp_char}]*(\"[^\"]*\"|'[^']*'|[^{sp_char}\"'=<>`/]+))?)".format(attr_name=attr_name, sp_char=sp_char)
    self.attr_pattern = re.compile(attr_pattern)
    attrs_pattern = "({attr_pattern})+".format(attr_pattern=attr_pattern) # tags with no attributes will not be considered.
    self.attrs_pattern = re.compile(attrs_pattern)

    tag_name = "[a-zA-Z0-9]"
    tag_pattern = "(<(?!/)({tag_name}+:{tag_name}+|({tag_name}+\-)*{tag_name}+){attrs_pattern}[{sp_char}]*/?>)".format(tag_name=tag_name, attrs_pattern=attrs_pattern, sp_char=sp_char)
    self.tag_pattern = tag_pattern

    self.priority = _get_setting("priority")

  def sort_attr(self, attrs):
    def _key(attr):
      try:
        weight = self.priority.index(attr[1])
      except ValueError:
        try:
          weight = self.priority.index("*")
        except ValueError:
          weight = len(self.priority)
      return (weight, attr[1])

    sorted_attrs = sorted(attrs, key=_key)
    return sorted_attrs

  def run(self, edit):
    current_syntax = self.view.settings().get("syntax")
    allowed_syntaxes = _get_setting("allowed_syntaxes")
    if all(map(lambda s: current_syntax.upper().find(s.upper()) == -1, allowed_syntaxes)): # do nothing if syntax not matched.
      return

    start_tags = self.view.find_all(self.tag_pattern)
    start_tags.reverse()
    for r in start_tags:
      start_tag = self.view.substr(r)
      start_tag_without_attr = self.attrs_pattern.sub("", start_tag)
      attr_start_from = self.attrs_pattern.search(start_tag).start()
      attrs = self.attr_pattern.findall(start_tag)
      attrs_sorted = [i[0] for i in self.sort_attr(attrs)]
      attrs_sorted.insert(0, "")
      new_start_tag = start_tag_without_attr[:attr_start_from] + " ".join(attrs_sorted) + start_tag_without_attr[attr_start_from:]
      self.view.replace(edit, r, new_start_tag)

class SortHtmlAttrOnSave(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    sort_on_save = _get_setting("sort_on_save")

    if sort_on_save:
      view.run_command("sort_html_attr")
