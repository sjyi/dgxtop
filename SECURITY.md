# Security Policy

## Supported Versions

We provide security updates for the following versions of DGXTOP:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest | :x:               |

We recommend always using the latest version of DGXTOP to ensure you have the most recent security fixes.

## Reporting a Vulnerability

We take security issues seriously. If you discover a security vulnerability in DGXTOP, please report it by opening a GitHub issue.

### How to Report

1. **Open a GitHub Issue**: Go to the [Issues](../../issues) page and create a new issue
2. **Use a clear title**: Start with "[SECURITY]" to help us identify it quickly
3. **Provide details**: Include as much information as possible:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Any suggested fixes (if you have them)

### What to Expect

- **Acknowledgment**: We aim to acknowledge security reports within one week
- **Updates**: We will keep you informed about our progress in addressing the issue
- **Resolution**: Once fixed, we will credit you in the release notes (unless you prefer to remain anonymous)

## Security Considerations

DGXTOP is a monitoring tool that reads system information. Here are some security considerations:

### What DGXTOP Accesses

- `/proc/diskstats` - Disk I/O statistics (read-only)
- `/proc/stat` and `/proc/meminfo` - CPU and memory statistics (read-only)
- `/sys/class/net/` - Network interface statistics (read-only)
- `nvidia-smi` - GPU information via NVIDIA's tool

### Permissions

- DGXTOP runs with the permissions of the user executing it
- No elevated privileges (root/sudo) are required for basic functionality
- Some GPU features may require appropriate NVIDIA driver permissions

### Data Handling

- DGXTOP does not collect, store, or transmit any data externally
- All monitoring data is displayed locally and discarded after display
- No configuration files contain sensitive information

## Best Practices

When using DGXTOP:

- Keep the tool updated to the latest version
- Run with minimal necessary permissions
- Review the source code if deploying in sensitive environments
