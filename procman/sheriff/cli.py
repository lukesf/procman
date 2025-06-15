import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box
import time
import json
from typing import Optional, List
from .sheriff import Sheriff


class SheriffCLI:
    """CLI interface for the Sheriff process manager."""
    
    def __init__(self):
        self.sheriff = Sheriff()
        self.console = Console()
    
    def generate_process_table(self) -> Table:
        """Generate a rich table with process information."""
        table = Table(
            "Name", "Host", "Status", "PID", "CPU %", "Memory %", "Uptime",
            box=box.ROUNDED,
            title="Process Status"
        )
        
        for process in self.sheriff.get_all_processes():
            uptime = ''
            if process.start_time:
                uptime_secs = int(process.to_dict()["uptime"])
                uptime = f'{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m {uptime_secs % 60}s'
            
            status_color = {
                "running": "green",
                "stopped": "red",
                "died": "red",
            }.get(process.status, "yellow")
            
            table.add_row(
                process.name,
                process.host,
                f"[{status_color}]{process.status}[/]",
                str(process.pid or ''),
                f"{process.cpu_percent:.1f}",
                f"{process.memory_percent:.1f}",
                uptime
            )
        
        return table
    
    def generate_deputy_table(self) -> Table:
        """Generate a rich table with deputy information."""
        table = Table(
            "Hostname", "URL", "Status", "CPU %", "Memory %", "Disk %",
            box=box.ROUNDED,
            title="Deputy Status"
        )
    
        for deputy in self.sheriff.get_deputy_status():
            status_color = "green" if deputy["status"] == "healthy" else "red"
            table.add_row(
                deputy["hostname"],
                deputy["url"],
                f"[{status_color}]{deputy['status']}[/]",
                f"{deputy.get('cpu_percent', 0):.1f}",
                f"{deputy.get('memory_percent', 0):.1f}",
                f"{deputy.get('disk_percent', 0):.1f}"
            )
        
        return table
    
    def generate_display(self) -> Table:
        """Generate all display tables."""
        t = Table(title="ProcMan Sheriff", box=None)
        t.add_row(self.generate_deputy_table())
        t.add_row(self.generate_process_table())
        return t

@click.group()
def cli():
    """Sheriff Process Manager CLI"""
    pass


@cli.command()
@click.argument('url')
def add_deputy(url: str):
    """Add a Deputy server."""
    sheriff_cli = SheriffCLI()
    if sheriff_cli.sheriff.add_deputy(url):
        click.echo(f"Successfully added Deputy at {url}")
    else:
        click.echo(f"Failed to add Deputy at {url}", err=True)


@cli.command()
@click.argument('hostname')
def remove_deputy(hostname: str):
    """Remove a Deputy server."""
    sheriff_cli = SheriffCLI()
    if sheriff_cli.sheriff.remove_deputy(hostname):
        click.echo(f"Successfully removed Deputy {hostname}")
    else:
        click.echo(f"Failed to remove Deputy {hostname}", err=True)


@cli.command()
@click.argument('config_file')
def load_config(config_file: str):
    """Load configuration from a JSON file."""
    sheriff_cli = SheriffCLI()
    try:
        sheriff_cli.sheriff.load_config(config_file)
        click.echo(f"Successfully loaded config from {config_file}")
    except Exception as e:
        click.echo(f"Failed to load config: {str(e)}", err=True)


@cli.command()
@click.argument('name')
@click.argument('command')
@click.argument('working_dir')
@click.argument('host')
@click.option('--autostart', is_flag=True, help="Start the process automatically")
def add_process(name: str, command: str, working_dir: str, host: str, autostart: bool):
    """Add and start a new process."""
    from ..common.process_info import ProcessInfo
    
    sheriff_cli = SheriffCLI()
    process = ProcessInfo(
        name=name,
        command=command,
        working_dir=working_dir,
        host=host,
        autostart=autostart
    )
    
    if sheriff_cli.sheriff.start_process(process):
        click.echo(f"Successfully started process {name}")
    else:
        click.echo(f"Failed to start process {name}", err=True)


@cli.command()
@click.argument('name')
def stop_process(name: str):
    """Stop a running process."""
    sheriff_cli = SheriffCLI()
    if sheriff_cli.sheriff.stop_process(name):
        click.echo(f"Successfully stopped process {name}")
    else:
        click.echo(f"Failed to stop process {name}", err=True)


@cli.command()
@click.argument('name')
def restart_process(name: str):
    """Restart a process."""
    sheriff_cli = SheriffCLI()
    if sheriff_cli.sheriff.restart_process(name):
        click.echo(f"Successfully restarted process {name}")
    else:
        click.echo(f"Failed to restart process {name}", err=True)


@cli.command()
@click.option('--refresh-rate', default=1.0, help="Refresh rate in seconds")
@click.argument('config_file')
def monitor(config_file: str, refresh_rate: float):
    """Monitor all processes in real-time."""
    sheriff_cli = SheriffCLI()
    sheriff_cli.sheriff.load_config(config_file)
    sheriff_cli.sheriff.start_update_thread(refresh_rate)
    
    try:
        with Live(
            sheriff_cli.generate_display(),
            refresh_per_second=4,
            screen=True
        ) as live:
            while True:
                live.update(sheriff_cli.generate_display())
                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        sheriff_cli.sheriff.stop_update_thread()


@cli.command()
def status():
    """Show status of all deputies and processes."""
    sheriff_cli = SheriffCLI()
    
    # Get deputy status
    deputies = sheriff_cli.sheriff.get_deputy_status()
    for deputy in deputies:
        status_color = "green" if deputy["status"] == "healthy" else "red"
        click.echo(f"Deputy {deputy['hostname']} ({deputy['url']}): {deputy['status']}")
    
    # Get process status
    processes = sheriff_cli.sheriff.get_all_processes()
    for process in processes:
        status_color = {
            "running": "green",
            "stopped": "red",
            "died": "red",
        }.get(process.status, "yellow")
        click.echo(f"Process {process.name} ({process.host}): {process.status}")
    
    return True


def main():
    """Start the Sheriff CLI application."""
    cli() 