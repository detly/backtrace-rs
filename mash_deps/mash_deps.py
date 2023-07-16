#!/usr/bin/env python3

def main():
    from functools import reduce
    import operator
    from tomlkit.toml_file import TOMLFile
    import tomlkit

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
        # Can't set the root by key, that would have to assign in the caller.
        get_by_keys(package_node, path[:-1])[path[-1]] = version

    DEPS = ["addr2line", "rustc-demangle", "miniz_oxide", "object"]   
    manifest_bt = TOMLFile("library/backtrace/Cargo.toml").read()
    
    deps_bt = {
        dep: get_by_keys(val, pth)
        for dep, val in manifest_bt["dependencies"].items()
        if dep in DEPS and (pth := version_path(val)) is not None
    }

    manifest_std = TOMLFile("library/std/Cargo.toml").read()
    deps_std = manifest_std["dependencies"]

    for (dep, ver) in deps_bt.items():
        if (dep_node := deps_std.get(dep)):
            path_from_deps_section = [dep] + version_path(dep_node)
            set_by_keys(deps_std, path_from_deps_section, ver)
            print(f"Patched {dep} = {ver} in std")

    TOMLFile("library/std/Cargo.toml").write(manifest_std)

if __name__ == "__main__":
    main()
