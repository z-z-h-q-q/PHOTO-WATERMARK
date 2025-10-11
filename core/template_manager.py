# template_manager.py
import json
import os

class TemplateManager:
    def __init__(self, template_file="templates.json", default_template="test1"):
        self.template_file = template_file
        self.default_template = default_template
        self.templates = self._load_templates()

        # 启动时加载默认模板
        self.current_template = self.templates.get(self.default_template, {})

    def _load_templates(self):
        if not os.path.exists(self.template_file):
            return {}
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载模板失败: {e}")
            return {}

    def save_template(self, name, properties):
        self.templates[name] = properties
        try:
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False

    def get_template(self, name):
        return self.templates.get(name)

    def list_templates(self):
        return list(self.templates.keys())

    def delete_template(self, name):
        if name in self.templates:
            del self.templates[name]
            try:
                with open(self.template_file, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"删除模板失败: {e}")
        return False
