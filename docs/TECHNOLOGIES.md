# TOR - Unveil: Technology Stack

## Complete List of Technologies, Libraries, and Tools

### Backend Technologies

#### Core Framework
- **Python 3.10+** - Programming language
- **FastAPI 0.104.1** - Modern web framework for building APIs
- **Uvicorn 0.24.0** - ASGI server for FastAPI
- **Pydantic 2.5.0** - Data validation using Python type annotations
- **Pydantic-Settings 2.1.0** - Settings management

#### Database & ORM
- **PostgreSQL 15** - Relational database
- **SQLAlchemy 2.0.23** - SQL toolkit and ORM
- **psycopg2-binary 2.9.9** - PostgreSQL adapter for Python
- **Alembic 1.13.0** - Database migration tool

#### Data Processing & Analysis
- **Pandas 2.1.4** - Data manipulation and analysis
- **NumPy 1.26.2** - Numerical computing
- **SciPy 1.11.4** - Scientific computing (distance metrics)

#### Correlation & Algorithms
- **FastDTW 0.3.4** - Dynamic Time Warping implementation
- Custom implementations:
  - Cosine similarity
  - Euclidean distance
  - Feature extraction algorithms
  - Probability scoring

#### HTTP & API
- **Requests 2.31.0** - HTTP library for API calls
- **aiohttp 3.9.1** - Async HTTP client/server
- **python-multipart 0.0.6** - Multipart form data parser

#### Environment & Configuration
- **python-dotenv 1.0.0** - Environment variable management

### Frontend Technologies

#### Core Framework
- **React 18.2.0** - JavaScript library for UI
- **TypeScript 4.9.5** - Typed superset of JavaScript
- **React-DOM 18.2.0** - React rendering for web
- **React Scripts 5.0.1** - Create React App build scripts

#### Visualization Libraries
- **D3.js 7.8.5** - Data visualization library
  - Used for: Circuit path diagram, custom SVG graphics
- **Recharts 2.10.3** - Chart library built on React and D3
  - Used for: Bar charts, probability distributions

#### HTTP Client
- **Axios 1.6.2** - Promise-based HTTP client

#### TypeScript Support
- **@types/react 18.2.45** - TypeScript definitions for React
- **@types/react-dom 18.2.18** - TypeScript definitions for React-DOM
- **@types/d3 7.4.3** - TypeScript definitions for D3.js
- **@types/node 16.18.68** - Node.js TypeScript definitions
- **@types/jest 27.5.2** - Jest TypeScript definitions

#### Testing
- **@testing-library/react 13.4.0** - React testing utilities
- **@testing-library/jest-dom 5.17.0** - Custom Jest matchers
- **@testing-library/user-event 13.5.0** - User event simulation

#### Build Tools
- **Webpack** (via React Scripts) - Module bundler
- **Babel** (via React Scripts) - JavaScript compiler
- **ESLint** (via React Scripts) - Code linting

### Database

#### Core Database
- **PostgreSQL 15-alpine** - Lightweight PostgreSQL Docker image

#### Extensions & Features
- **uuid-ossp** - UUID generation extension
- **JSON/JSONB** - Native JSON support for flexible data storage

### Infrastructure & DevOps

#### Containerization
- **Docker** - Container platform
- **Docker Compose** - Multi-container orchestration
  - Version: 3.8

#### Container Images
- **python:3.10-slim** - Minimal Python base image
- **node:18-alpine** - Minimal Node.js base image
- **postgres:15-alpine** - Minimal PostgreSQL image

#### System Dependencies
- **gcc** - C compiler (for Python extensions)
- **postgresql-client** - PostgreSQL command-line tools

### Development Tools

#### Version Control
- **Git** - Version control system
- **.gitignore** - Git ignore configuration

#### Environment Management
- **.env** - Environment variables
- **.env.example** - Example configuration

#### Scripts
- **start.bat** - Windows startup script
- **stop.bat** - Windows stop script

### Documentation Tools

#### Formats
- **Markdown** - Documentation format
- **ReStructuredText** - Python documentation

#### Auto-Generated
- **OpenAPI/Swagger** - API documentation (via FastAPI)
- **JSDoc** - JavaScript documentation

### Networking & Protocols

#### Protocols
- **HTTP/HTTPS** - Web protocols
- **TCP/IP** - Transport protocols
- **REST** - API architecture
- **JSON** - Data interchange format

#### CORS
- **FastAPI CORS Middleware** - Cross-origin resource sharing

### External APIs

#### Data Sources
- **Tor Onionoo API** - Public Tor relay directory
  - Endpoint: https://onionoo.torproject.org
  - No authentication required
  - Public data only

### Security & Authentication

#### Current Implementation
- No authentication (MVP)
- CORS enabled for local development
- Environment-based secrets management

### Algorithms Implemented

#### Traffic Analysis
- **Burst Detection** - Custom threshold-based algorithm
- **Feature Extraction** - Statistical feature computation
- **Inter-packet Delay Analysis** - Timing analysis

#### Correlation Methods
- **Dynamic Time Warping (DTW)** - Time-series similarity
- **Cosine Similarity** - Vector similarity
- **Euclidean Distance** - Geometric similarity
- **Weighted Scoring** - Multi-metric combination

#### Statistical Methods
- **Mean, Median, Standard Deviation** - Basic statistics
- **Min-Max Normalization** - Feature scaling
- **Percentile Calculation** - Distribution analysis

### Design Patterns

#### Backend Patterns
- **Repository Pattern** - Data access abstraction
- **Service Layer** - Business logic separation
- **Dependency Injection** - FastAPI's dependency system
- **MVC Architecture** - Model-View-Controller

#### Frontend Patterns
- **Component-Based Architecture** - React components
- **Container/Presenter Pattern** - Smart/dumb components
- **Service Pattern** - API client abstraction
- **Hooks Pattern** - React hooks for state management

### Standards & Conventions

#### Code Style
- **PEP 8** - Python style guide
- **ESLint** - JavaScript/TypeScript linting
- **Type Hints** - Python type annotations
- **TypeScript Strict Mode** - Enhanced type checking

#### API Standards
- **RESTful API** - REST architecture principles
- **OpenAPI 3.0** - API specification standard
- **JSON API** - JSON data format

#### Database Standards
- **ACID Compliance** - PostgreSQL transactions
- **Normalization** - Database design principles
- **Indexing** - Query optimization

### License Information

#### Software Licenses
- **MIT License** - Primary project license
- **BSD License** - NumPy, Pandas, D3.js
- **Apache License 2.0** - Requests, TypeScript, Docker

#### Compliance
- All dependencies are open-source
- No proprietary dependencies
- No paid services required

### Performance Optimizations

#### Backend
- **Async/Await** - Asynchronous processing
- **Connection Pooling** - Database connections
- **Lazy Loading** - SQLAlchemy relationships

#### Frontend
- **Code Splitting** - Webpack optimization
- **Lazy Loading** - Component loading
- **Memoization** - React optimization

#### Database
- **Indexes** - Query performance
- **Connection Pooling** - Resource management

### Monitoring & Logging

#### Logging
- **Python logging** - Built-in logging module
- **Log levels** - INFO, WARNING, ERROR, DEBUG

#### Monitoring
- **Docker stats** - Container resource monitoring
- **PostgreSQL logs** - Database activity logs

### Browser Support

#### Supported Browsers
- **Chrome** - Latest 2 versions
- **Firefox** - Latest 2 versions
- **Safari** - Latest 2 versions
- **Edge** - Latest 2 versions

#### Required Features
- **ES6+** - Modern JavaScript features
- **CSS Grid** - Layout support
- **Flexbox** - Flexible layouts
- **SVG** - Vector graphics

### System Requirements

#### Development Environment
- **OS**: Windows 10+, macOS 10.15+, Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space
- **Docker**: Latest stable version

#### Production Environment
- **RAM**: 2GB minimum
- **CPU**: 2 cores minimum
- **Disk**: 5GB for data storage
- **Network**: Internet (for live mode only)

---

## Version Summary

**Project Version**: 1.0.0
**Python Version**: 3.10+
**Node Version**: 18+
**PostgreSQL Version**: 15
**Docker Compose Version**: 3.8

**Last Updated**: December 13, 2025
