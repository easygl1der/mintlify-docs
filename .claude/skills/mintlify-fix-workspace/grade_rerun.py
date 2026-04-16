import os
import json
import re

def grade_eval_1(output_dir):
    results = []

    # 1. Validation successful
    log_path = os.path.join(output_dir, "mintlify-validate-output.txt")
    if not os.path.exists(log_path):
        # try common fallback names
        log_path = os.path.join(output_dir, "validation_output.txt")

    passed_validation = False
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            content = f.read()
            if "Validation successful!" in content:
                passed_validation = True

    results.append({
        "text": "The final output of mintlify validate contains 'Validation successful!'",
        "passed": passed_validation,
        "evidence": "Found 'Validation successful!' in log" if passed_validation else "Log missing or success message not found"
    })

    # Check error-page.mdx
    mdx_path = os.path.join(output_dir, "test-docs/error-page.mdx")
    if os.path.exists(mdx_path):
        with open(mdx_path, 'r') as f:
            content = f.read()

            # 2. Description quoted
            # Frontmatter looks like: description: "..."
            desc_match = re.search(r'^description:\s*"(.*)"', content, re.MULTILINE)
            passed_desc = desc_match is not None
            results.append({
                "text": "The description in test-docs/error-page.mdx is quoted",
                "passed": passed_desc,
                "evidence": "Found quoted description" if passed_desc else "Description not quoted or not found"
            })

            # 3. <3.0.0 in backticks
            passed_backticks = "`<3.0.0`" in content
            results.append({
                "text": "The <3.0.0 string in test-docs/error-page.mdx is wrapped in backticks",
                "passed": passed_backticks,
                "evidence": "Found `<3.0.0`" if passed_backticks else "`<3.0.0` not found"
            })

            # 4. <br> to <br/>
            passed_br = "<br/>" in content and "<br>" not in content.replace("<br/>", "")
            results.append({
                "text": "The <br> tag in test-docs/error-page.mdx is converted to <br/>",
                "passed": passed_br,
                "evidence": "Found <br/> and no unclosed <br>" if passed_br else "Found unclosed <br> or missing <br/>"
            })

            # 5. Table closing pipes
            # Check lines starting with | and ending with |
            table_lines = [l for l in content.split('\n') if l.strip().startswith('|')]
            passed_pipes = all(l.strip().endswith('|') for l in table_lines) if table_lines else False
            results.append({
                "text": "The table in test-docs/error-page.mdx is properly formatted with closing pipes",
                "passed": passed_pipes,
                "evidence": "All table lines end with |" if passed_pipes else "Some table lines missing closing pipe"
            })
    else:
        for i in range(4):
            results.append({"text": "File check", "passed": False, "evidence": "error-page.mdx not found"})

    return results

def grade_eval_2(output_dir):
    results = []

    # 1. Validation successful
    log_path = os.path.join(output_dir, "mintlify-validate-output.txt")
    if not os.path.exists(log_path):
        log_path = os.path.join(output_dir, "mintlify_validate.log")

    passed_validation = False
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            content = f.read()
            if "Validation successful!" in content:
                passed_validation = True

    results.append({
        "text": "The final output of mintlify validate contains 'Validation successful!'",
        "passed": passed_validation,
        "evidence": "Found 'Validation successful!' in log" if passed_validation else "Log missing or success message not found"
    })

    # 2. openscreen.md fix
    md_path = os.path.join(output_dir, "trending/2026-04-16/openscreen.md")
    passed_fix = False
    if os.path.exists(md_path):
        with open(md_path, 'r') as f:
            content = f.read()
            # Check if unescaped < in version numbers or tags are gone
            # In openscreen.md it was likely something like <2.0.0
            if "<" not in content or "`<" in content or " &lt; " in content:
                passed_fix = True

    results.append({
        "text": "The unescaped tag error in trending/2026-04-16/openscreen.md is fixed",
        "passed": passed_fix,
        "evidence": "Tag escaped or hidden" if passed_fix else "Unescaped tag still present"
    })

    return results

def main():
    base_dir = "/Volumes/SSK SSD/Projects/mintlify-docs/.claude/skills/mintlify-fix-workspace/iteration-1"

    for eval_id in [1, 2]:
        for config in ["with_skill", "without_skill"]:
            run_dir = os.path.join(base_dir, f"eval-{eval_id}", config)
            output_dir = os.path.join(run_dir, "outputs")

            if not os.path.exists(output_dir):
                continue

            if eval_id == 1:
                results = grade_eval_1(output_dir)
            else:
                results = grade_eval_2(output_dir)

            with open(os.path.join(run_dir, "grading.json"), "w") as f:
                json.dump({"expectations": results}, f, indent=2)

if __name__ == "__main__":
    main()
