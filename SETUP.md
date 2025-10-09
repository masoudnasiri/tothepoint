# Procurement DSS Setup Guide

This guide will help you set up and run the Project Procurement & Financial Optimization Decision Support System.

## Prerequisites

Before starting, ensure you have the following installed:

- **Docker** (version 20.10 or later)
- **Docker Compose** (version 2.0 or later)
- **Git** (for cloning the repository)

### Installing Prerequisites

#### Docker Installation
- **Windows**: Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- **macOS**: Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow the [official Docker installation guide](https://docs.docker.com/engine/install/)

#### Docker Compose
Docker Compose is included with Docker Desktop. For Linux installations, you may need to install it separately.

## Quick Start (Recommended)

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd cahs_flow_project
   ```

2. **Make startup scripts executable** (Linux/macOS)
   ```bash
   chmod +x start.sh stop.sh
   ```

3. **Start the system**
   ```bash
   ./start.sh
   ```
   
   Or on Windows:
   ```cmd
   start.sh
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Setup

If you prefer to run the setup manually:

1. **Start the database**
   ```bash
   docker-compose up -d postgres
   ```

2. **Wait for database to be ready** (about 30 seconds)

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

## Default Login Credentials

The system comes with pre-configured users for testing:

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | admin | admin123 | Full system access |
| Project Manager | pm1 | pm123 | Project and item management |
| Procurement Specialist | proc1 | proc123 | Procurement options management |
| Finance User | finance1 | finance123 | Budget and optimization |

## System Architecture

The system consists of three main components:

### Backend (FastAPI)
- **Port**: 8000
- **Technology**: Python 3.11, FastAPI, SQLAlchemy, OR-Tools
- **Features**: REST API, JWT authentication, optimization engine

### Frontend (React)
- **Port**: 3000
- **Technology**: React 18, TypeScript, Material-UI
- **Features**: Responsive UI, role-based access, Excel import/export

### Database (PostgreSQL)
- **Port**: 5432
- **Technology**: PostgreSQL 15
- **Features**: Persistent data storage, sample data

## Development Setup

For development work, you can run the services separately:

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## Configuration

### Environment Variables

The system uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (change in production)
- `ENVIRONMENT`: development/production
- `DEBUG`: Enable debug mode

### Database Configuration

The database is automatically initialized with:
- Sample projects and users
- Procurement options
- Budget data
- Project items

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Ensure ports 3000, 8000, and 5432 are not in use
   - Change ports in `docker-compose.yml` if needed

2. **Docker not running**
   - Start Docker Desktop
   - Ensure Docker daemon is running

3. **Database connection issues**
   - Wait for PostgreSQL to fully start (30-60 seconds)
   - Check database logs: `docker-compose logs postgres`

4. **Frontend not loading**
   - Check if backend is running: `docker-compose logs backend`
   - Verify API URL configuration

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Resetting the System

To reset all data and start fresh:

```bash
docker-compose down -v
docker-compose up --build
```

## Production Deployment

For production deployment:

1. **Change default passwords** and secret keys
2. **Use environment variables** for configuration
3. **Set up proper SSL/TLS** certificates
4. **Configure database backups**
5. **Use a production-grade database** (not the Docker PostgreSQL)

## API Documentation

Once the system is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify all prerequisites are installed
3. Ensure Docker has sufficient resources allocated
4. Review the API documentation for endpoint details

## System Requirements

### Minimum Requirements
- 4GB RAM
- 2 CPU cores
- 10GB free disk space
- Docker with 2GB memory allocation

### Recommended Requirements
- 8GB RAM
- 4 CPU cores
- 20GB free disk space
- Docker with 4GB memory allocation
