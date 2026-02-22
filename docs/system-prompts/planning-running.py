#!/usr/bin/env python3
"""
Inspect running AI agent processes (Claude, Gemini, Codex, Cline) and their context.

Provides intuitive information about:
- Which agents are currently running
- What projects/directories they're working in
- Open files and activity
- Process tree relationships
- Which agent is calling this script (self-identification)

Helps agents understand the landscape and make informed decisions about
bead ownership, stalling detection, and multi-terminal coordination.
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Set
from datetime import datetime


@dataclass
class ProcessInfo:
    """Information about a running agent process."""
    pid: int
    name: str  # claude, gemini, codex, cline
    ppid: int
    cmd: str
    cwd: str
    terminal: str
    elapsed: str
    open_files: List[str]
    projects: List[str]  # inferred from paths
    is_self: bool = False  # is this the calling process?

    def to_dict(self):
        return asdict(self)


class AgentProcessInspector:
    """Inspects and reports on running AI agent processes."""

    AGENT_PATTERNS = {
        'claude': re.compile(r'claude(?:\s|$)'),
        'gemini': re.compile(r'gemini'),
        'codex': re.compile(r'codex'),
        'cline': re.compile(r'cline'),
    }

    HENTOWN_PROJECTS = {
        'hentown': '/home/phaedrus/hentown',
        'mellona': '/home/phaedrus/hentown/modules/mellona',
        'second_voice': '/home/phaedrus/hentown/modules/second_voice',
        'pigeon': '/home/phaedrus/hentown/modules/pigeon',
        'hatchery': '/home/phaedrus/hentown/modules/hatchery',
        'chatterbox': '/home/phaedrus/hentown/modules/chatterbox',
        'chatvault': '/home/phaedrus/hentown/modules/chatvault',
        'logist': '/home/phaedrus/hentown/modules/logist',
        'oneshot': '/home/phaedrus/hentown/modules/oneshot',
        'whisper': '/home/phaedrus/hentown/modules/whisper',
        'google-personal-mcp': '/home/phaedrus/hentown/modules/google-personal-mcp',
        'slack-agent-mcp': '/home/phaedrus/hentown/modules/slack-agent-mcp',
    }

    def __init__(self):
        self.my_ppid = os.getppid()  # Parent of current process
        self.my_pid = os.getpid()
        self.processes: List[ProcessInfo] = []

    def get_all_processes(self) -> List[Dict]:
        """Get list of all processes from ps."""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.split('\n')[1:]  # skip header
            processes = []
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        'user': parts[0],
                        'pid': int(parts[1]),
                        'cpu': parts[2],
                        'mem': parts[3],
                        'vsz': parts[4],
                        'rss': parts[5],
                        'tty': parts[6],
                        'stat': parts[7],
                        'start': parts[8],
                        'time': parts[9],
                        'cmd': parts[10] if len(parts) > 10 else '',
                    })
            return processes
        except Exception as e:
            print(f"Error getting process list: {e}", file=sys.stderr)
            return []

    def identify_agent_type(self, cmd: str) -> Optional[str]:
        """Identify which AI agent this process is."""
        for agent_name, pattern in self.AGENT_PATTERNS.items():
            if pattern.search(cmd):
                return agent_name
        return None

    def get_cwd(self, pid: int) -> str:
        """Get current working directory of process."""
        try:
            cwd_path = Path(f'/proc/{pid}/cwd')
            if cwd_path.exists():
                return str(cwd_path.resolve())
        except Exception:
            pass
        return "unknown"

    def get_open_files(self, pid: int, limit: int = 20) -> List[str]:
        """Get open files for a process (lsof)."""
        try:
            result = subprocess.run(
                ['lsof', '-p', str(pid)],
                capture_output=True,
                text=True,
                timeout=5
            )
            files = []
            for line in result.stdout.split('\n')[1:]:  # skip header
                parts = line.split()
                if len(parts) >= 9:
                    filepath = ' '.join(parts[8:])
                    # Filter to user files, ignore libs/pipes
                    if filepath.startswith('/home') or filepath.startswith('/tmp'):
                        if not any(x in filepath for x in ['.so', '.a', '.o']):
                            files.append(filepath)
            return files[:limit]
        except Exception:
            return []

    def infer_projects(self, cwd: str, files: List[str]) -> List[str]:
        """Infer which hentown projects this process is working on."""
        projects = []
        search_paths = [cwd] + files

        for path in search_paths:
            for proj_name, proj_path in self.HENTOWN_PROJECTS.items():
                if proj_path in path:
                    if proj_name not in projects:
                        projects.append(proj_name)
                    break
        return projects

    def get_ppid(self, pid: int) -> int:
        """Get parent PID."""
        try:
            result = subprocess.run(
                ['ps', '-o', 'ppid=', '-p', str(pid)],
                capture_output=True,
                text=True,
                timeout=2
            )
            return int(result.stdout.strip())
        except Exception:
            return -1

    def get_terminal(self, tty: str) -> str:
        """Format terminal info."""
        if tty == '?':
            return 'background'
        return f'terminal:{tty}'

    def scan_agents(self) -> List[ProcessInfo]:
        """Scan for all running agent processes."""
        processes = self.get_all_processes()
        agents = []

        for proc in processes:
            agent_type = self.identify_agent_type(proc['cmd'])
            if not agent_type:
                continue

            pid = proc['pid']
            cwd = self.get_cwd(pid)
            files = self.get_open_files(pid)
            projects = self.infer_projects(cwd, files)
            ppid = self.get_ppid(pid)

            is_self = (ppid == self.my_ppid)  # same parent = likely me

            agent = ProcessInfo(
                pid=pid,
                name=agent_type,
                ppid=ppid,
                cmd=proc['cmd'],
                cwd=cwd,
                terminal=self.get_terminal(proc['tty']),
                elapsed=proc['time'],
                open_files=files,
                projects=projects,
                is_self=is_self,
            )
            agents.append(agent)

        self.processes = sorted(agents, key=lambda x: (not x.is_self, x.pid))
        return self.processes

    def format_report(self, detailed: bool = False) -> str:
        """Format the report as intuitive output."""
        if not self.processes:
            return "No running AI agent processes found.\n"

        lines = []
        lines.append("=" * 80)
        lines.append("RUNNING AI AGENT PROCESSES")
        lines.append("=" * 80)
        lines.append("")

        # Self identification
        self_proc = None
        for proc in self.processes:
            if proc.is_self:
                self_proc = proc
                lines.append(f"ℹ️  THIS SCRIPT IS RUNNING IN: {proc.name.upper()} (PID {proc.pid})")
                lines.append(f"   Parent: PID {proc.ppid}")
                lines.append(f"   Terminal: {proc.terminal}")
                lines.append(f"   Working Dir: {proc.cwd}")
                if proc.projects:
                    lines.append(f"   Projects: {', '.join(proc.projects)}")
                lines.append("")
                break

        if not self_proc:
            lines.append("⚠️  Could not identify this script as running in a known agent process")
            lines.append("")

        # Other processes
        other_agents = [p for p in self.processes if not p.is_self]
        if other_agents:
            lines.append("OTHER RUNNING AGENTS:")
            lines.append("-" * 80)
            for proc in other_agents:
                lines.append(f"\n🔷 {proc.name.upper()} (PID {proc.pid})")
                lines.append(f"   Parent PID: {proc.ppid}")
                lines.append(f"   Terminal: {proc.terminal}")
                lines.append(f"   Elapsed: {proc.elapsed}")
                lines.append(f"   Working Dir: {proc.cwd}")

                if proc.projects:
                    lines.append(f"   Projects: {', '.join(proc.projects)}")

                if detailed and proc.open_files:
                    lines.append(f"   Open Files:")
                    for f in proc.open_files[:5]:
                        lines.append(f"     - {f}")
                    if len(proc.open_files) > 5:
                        lines.append(f"     ... and {len(proc.open_files) - 5} more")
        else:
            lines.append("(No other agents currently running)")

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def to_json(self) -> str:
        """Output as JSON for programmatic use."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'self': {
                'pid': self.my_pid,
                'ppid': self.my_ppid,
            },
            'agents': [p.to_dict() for p in self.processes],
        }
        return json.dumps(data, indent=2)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Inspect running AI agent processes'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of human-readable format'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information (open files, etc.)'
    )
    parser.add_argument(
        '--self-only',
        action='store_true',
        help='Show only the calling process'
    )

    args = parser.parse_args()

    inspector = AgentProcessInspector()
    inspector.scan_agents()

    if args.json:
        print(inspector.to_json())
    else:
        report = inspector.format_report(detailed=args.detailed)
        print(report)

        if args.self_only:
            for proc in inspector.processes:
                if proc.is_self:
                    print(f"\nSelf Identification: {proc.name} (PID {proc.pid})")
                    if proc.projects:
                        print(f"Working on projects: {', '.join(proc.projects)}")
                    break


if __name__ == '__main__':
    main()
