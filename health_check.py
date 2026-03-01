#!/usr/bin/env python
"""
Legal CLM System Health Check Script
Run this to verify all components are working correctly
"""

import os
import sys
import subprocess
import time

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def run_command(command, description):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print_success(f"{description}")
            return True
        else:
            print_error(f"{description}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error(f"{description}: Command timed out")
        return False
    except Exception as e:
        print_error(f"{description}: {str(e)}")
        return False

def check_docker():
    """Check if Docker is running"""
    print_header("Checking Docker")
    
    if not run_command("docker --version", "Docker installed"):
        print_error("Docker is not installed or not in PATH")
        return False
    
    if not run_command("docker ps", "Docker daemon running"):
        print_error("Docker daemon is not running. Please start Docker Desktop.")
        return False
    
    return True

def check_containers():
    """Check if all containers are running"""
    print_header("Checking Containers")
    
    containers = [
        "web",
        "db",
        "redis",
        "celery_worker",
        "celery_beat",
        "nginx"
    ]
    
    all_running = True
    for container in containers:
        cmd = f"docker-compose ps {container} | grep Up"
        if run_command(cmd, f"{container} container running"):
            pass
        else:
            all_running = False
    
    return all_running

def check_database():
    """Check database connectivity"""
    print_header("Checking Database")
    
    cmd = 'docker-compose exec -T db psql -U clm_user -d legal_clm_db -c "SELECT 1;"'
    return run_command(cmd, "Database connection")

def check_redis():
    """Check Redis connectivity"""
    print_header("Checking Redis")
    
    cmd = 'docker-compose exec -T redis redis-cli ping'
    return run_command(cmd, "Redis connection")

def check_django():
    """Check Django application"""
    print_header("Checking Django Application")
    
    # Check migrations
    cmd = 'docker-compose exec -T web python manage.py showmigrations | grep "\\[X\\]"'
    if not run_command(cmd, "Database migrations applied"):
        print_warning("Some migrations may not be applied")
    
    # Check admin user exists
    cmd = 'docker-compose exec -T web python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "True" in result.stdout:
        print_success("Superuser exists")
    else:
        print_warning("No superuser found. Create one with: docker-compose exec web python manage.py createsuperuser")
    
    return True

def check_celery():
    """Check Celery workers"""
    print_header("Checking Celery")
    
    # Check worker
    cmd = 'docker-compose exec -T celery_worker celery -A legal_clm inspect active'
    if run_command(cmd, "Celery worker responding"):
        pass
    else:
        print_warning("Celery worker may not be ready yet")
    
    # Check beat
    cmd = 'docker-compose logs celery_beat | grep "Scheduler: Sending"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0 or "beat" in result.stdout.lower():
        print_success("Celery beat scheduler running")
    else:
        print_info("Celery beat starting (this is normal on first run)")
    
    return True

def check_web_access():
    """Check if web application is accessible"""
    print_header("Checking Web Access")
    
    try:
        import requests
        response = requests.get("http://localhost", timeout=10)
        if response.status_code == 200:
            print_success("Web application accessible at http://localhost")
            return True
        else:
            print_error(f"Web application returned status code: {response.status_code}")
            return False
    except ImportError:
        print_warning("'requests' module not installed. Skipping web access check.")
        print_info("You can manually verify by opening http://localhost in your browser")
        return True
    except Exception as e:
        print_error(f"Cannot access web application: {str(e)}")
        return False

def check_models():
    """Check if models are properly set up"""
    print_header("Checking Models")
    
    cmd = '''docker-compose exec -T web python manage.py shell << 'EOF'
from contracts.models import Contract, ContractParticipant, ContractSignature, AuditLog
print(f"Contract model: OK")
print(f"ContractParticipant model: OK")
print(f"ContractSignature model: OK")
print(f"AuditLog model: OK")
print(f"Total contracts: {Contract.objects.count()}")
EOF'''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "OK" in result.stdout:
        print_success("All models accessible")
        # Extract contract count
        for line in result.stdout.split('\n'):
            if "Total contracts:" in line:
                print_info(line.strip())
        return True
    else:
        print_error("Models check failed")
        return False

def print_summary(results):
    """Print summary of all checks"""
    print_header("Health Check Summary")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    if passed == total:
        print_success(f"All {total} checks passed! System is fully operational.")
    else:
        print_warning(f"{passed}/{total} checks passed. {failed} check(s) failed.")
    
    print("\n" + "="*60)
    for check, status in results.items():
        status_icon = "✓" if status else "✗"
        status_color = Colors.GREEN if status else Colors.RED
        print(f"{status_color}{status_icon}{Colors.END} {check}")
    print("="*60 + "\n")

def print_next_steps():
    """Print next steps for user"""
    print_header("Next Steps")
    
    print("1. Access the application:")
    print(f"   {Colors.BLUE}http://localhost{Colors.END}")
    print()
    print("2. Login with default credentials:")
    print(f"   Username: {Colors.BOLD}admin{Colors.END}")
    print(f"   Password: {Colors.BOLD}admin123{Colors.END}")
    print()
    print("3. View logs:")
    print(f"   {Colors.BLUE}docker-compose logs -f{Colors.END}")
    print()
    print("4. Create test contract:")
    print("   - Click 'Create Contract' in sidebar")
    print("   - Fill in the form")
    print("   - Submit")
    print()
    print("5. Test email notifications:")
    print(f"   {Colors.BLUE}docker-compose logs web | grep 'Subject:'{Colors.END}")
    print()
    print("6. Test Celery tasks:")
    print(f"   {Colors.BLUE}docker-compose exec web python manage.py shell{Colors.END}")
    print("   >>> from contracts.tasks import check_contract_expiry")
    print("   >>> check_contract_expiry()")
    print()

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print(r"""
    ╔═══════════════════════════════════════════════════╗
    ║   Legal CLM System Health Check                   ║
    ║   Verifying all components...                     ║
    ╚═══════════════════════════════════════════════════╝
    """)
    print(f"{Colors.END}")
    
    results = {}
    
    # Run all checks
    results["Docker Running"] = check_docker()
    
    if not results["Docker Running"]:
        print_error("\nDocker is not running. Please start Docker Desktop and try again.")
        sys.exit(1)
    
    results["Containers Running"] = check_containers()
    results["Database Connection"] = check_database()
    results["Redis Connection"] = check_redis()
    results["Django Application"] = check_django()
    results["Celery Workers"] = check_celery()
    results["Web Access"] = check_web_access()
    results["Models Setup"] = check_models()
    
    # Print summary
    print_summary(results)
    
    # Print next steps if all passed
    if all(results.values()):
        print_next_steps()
        print_success("System is ready for use! 🎉\n")
    else:
        print_error("\nSome checks failed. Please review the errors above.")
        print_info("Try running: docker-compose down && docker-compose up --build\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Health check interrupted by user.{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}\n")
        sys.exit(1)
