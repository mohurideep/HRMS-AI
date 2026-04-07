

def parse_swagger(swagger: dict):
    tools = []

    paths = swagger.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():

            if method.lower() not in ["get", "post"]:
                continue  # safety

            tool = {
                "name": generate_tool_name(method, path),
                "description": details.get("summary", f"{method.upper()} {path}"),
                "method": method.upper(),
                "path": path,
                "parameters": extract_parameters(details)
            }

            tools.append(tool)

    return tools


def generate_tool_name(method, path):
    parts = path.strip("/").split("/")
    return f"{method.lower()}_" + "_".join(parts[-2:])


def extract_parameters(details):
    params = []

    for p in details.get("parameters", []):
        params.append({
            "name": p.get("name"),
            "in": p.get("in"),
            "required": p.get("required", False),
            "type": p.get("schema", {}).get("type", "string")
        })

    return params