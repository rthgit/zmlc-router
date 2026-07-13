# Versioning and Compatibility

ZMLC uses semantic versioning. The 0.x MCP schemas may change with release notes. From
1.0 onward, tool names, required input fields, route names, and the solver protocol are
stable within the major version.

Additive optional fields are backward compatible. Removing a tool or required field
uses a deprecation period of at least one minor release. Every breaking change includes
a migration note and preserves the previous signed release for rollback.
