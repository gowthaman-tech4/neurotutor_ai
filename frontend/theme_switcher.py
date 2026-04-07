import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Remove all emojis (a comprehensive regex for emojis)
    # This regex covers most standard emoji blocks
    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])|"  # flags (iOS)
        u"([\u2600-\u26FF\u2700-\u27BF])|" # misc symbols and dingbats
        u"([\u2190-\u21FF\u2B00-\u2BFF\u2300-\u23FF])|" # arrows and tech symbols
        u"(\ud83e[\udd00-\uddff])|"  # Supplemental Symbols and Pictographs
        u"(\ud83e[\ude00-\udeff])|"  # Symbols and Pictographs Extended-A
        u"(\ud83e[\udf00-\udfff])|"  # Symbols and Pictographs Extended-A
        u"(\u200d\ud83c[\udf00-\udfff])|" # modifiers
        u"(\ufe0f)", flags=re.UNICODE)
    
    content = emoji_pattern.sub(r'', content)

    # 2. Color Refactoring for Light Theme + Dark Green Accents
    # Text colors
    content = content.replace("text-white", "text-gray-900")
    content = content.replace("text-gray-100", "text-gray-900")
    content = content.replace("text-gray-200", "text-gray-800")
    content = content.replace("text-gray-300", "text-gray-700")
    content = content.replace("text-gray-400", "text-gray-600")
    # Invert some dark text back to light if it was on a dark background (optional nuances)

    # Backgrounds & Opacities
    content = content.replace("bg-white/5", "bg-black/5")
    content = content.replace("bg-white/10", "bg-black/10")
    content = content.replace("bg-white/20", "bg-black/20")
    content = content.replace("hover:bg-white/5", "hover:bg-black/5")
    content = content.replace("hover:bg-white/10", "hover:bg-black/10")
    content = content.replace("border-white/5", "border-black/5")
    content = content.replace("border-white/10", "border-black/10")
    content = content.replace("border-white/20", "border-black/20")

    # Primary colors to Dark Green/Emerald
    content = content.replace("violet-", "emerald-")
    content = content.replace("purple-", "green-")
    content = content.replace("cyan-", "teal-")
    content = content.replace("blue-", "emerald-")

    # 3. Clean up any weird double spaces caused by emoji removal
    content = content.replace("  ", " ")

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

def main():
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts')):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
