#!/usr/bin/env python3

def main():
    import operator, os, tomlkit
    from functools import reduce
    from tomlkit.toml_file import TOMLFile

    # The deps to patch can't always be inferred by comparing manifests. Require
    # the workflow to specify them via this env var.
    DEPS_ENV_NAME = "PATCH_DEPS"

    deps_to_patch = os.environ.get(DEPS_ENV_NAME, "").split()

    if not len(deps_to_patch):
        raise SystemExit(f"Environment variable {DEPS_ENV_NAME} is not set")

    # These functions allow finding a "path" (list of keys) to the version key
    # in the TOML doc, and getting/setting via that path.

    def version_path(package_node):
        match package_node:
            case tomlkit.items.String(version):
                # packagename = "a.b.c"
                return []
            case tomlkit.items.AbstractTable(table):
                # packagename = { version = "a.b.c" } (or full table)
                return ["version"]
            case _:
                return None

    def get_by_keys(package_node, path):
        return reduce(operator.getitem, path, package_node)

    def set_by_keys(package_node, path, version):
        get_by_keys(package_node, path[:-1])[path[-1]] = version

    manifest_bt = TOMLFile("library/backtrace/Cargo.toml").read()
    
    deps_bt = {
        dep: get_by_keys(val, pth)
        for dep, val in manifest_bt["dependencies"].items()
        if dep in deps_to_patch and (pth := version_path(val)) is not None
    }

    manifest_std = TOMLFile("library/std/Cargo.toml").read()
    deps_std = manifest_std["dependencies"]

    for (dep, ver) in deps_bt.items():
        if (dep_node := deps_std.get(dep)):
            # Can't set the root by key, that would have to assign in the
            # caller. So prefix with dependency name key and start one level up.
            path_from_deps_section = [dep] + version_path(dep_node)
            ver_old = get_by_keys(deps_std, path_from_deps_section)
            set_by_keys(deps_std, path_from_deps_section, ver)
            print(f"Patched {dep} = {ver} from {ver_old} in std")

    TOMLFile("library/std/Cargo.toml").write(manifest_std)

if __name__ == "__main__":
    main()
