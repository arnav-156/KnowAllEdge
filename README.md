# KnowAllEdge

An AI-powered learning platform that transforms any topic into an interactive knowledge graph with comprehensive study tools, gamification, and analytics.

## 🌟 Features

### Core Features
- **AI-Powered Content Generation**: Generate comprehensive subtopics, flashcards, and quizzes using Google's Gemini AI
- **Interactive Knowledge Graphs**: Visualize learning paths with multiple view modes (3D, hierarchical, timeline, linear)
- **Smart Study Tools**: Flashcards, quizzes, Cornell notes, Pomodoro timer, and spaced repetition
- **Gamification System**: Achievements, skill trees, leaderboards, streaks, and challenge modes
- **Learning Analytics**: Track progress, identify knowledge gaps, and get personalized insights

### Advanced Features
- **Multi-language Support**: Full i18n with 6 languages (English, Spanish, French, German, Japanese, Chinese)
- **Offline Support**: PWA with service workers for offline access
- **Social Features**: Share knowledge graphs, embed in websites
- **Export Options**: PDF, Markdown, Anki, Notion, and more
- **Integration Ecosystem**: Connect with popular learning platforms

### Production-Ready Features
- **Security**: JWT authentication, RBAC, CSRF protection, secure headers, HTTPS enforcement
- **Performance**: Multi-layer caching, code splitting, lazy loading, compression
- **Monitoring**: Prometheus metrics, centralized logging, anomaly detection, alerting
- **Scalability**: Horizontal scaling, load balancing, auto-scaling
- **Testing**: 80%+ test coverage with unit, integration, and property-based tests

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run database migrations
python -m alembic upgrade head

# Start the server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Documentation

- [Quick Start Guide](QUICK_START.md)
- [Production Deployment](QUICK_START_PRODUCTION.md)
- [Security Guide](SECURITY_IMPLEMENTATION_GUIDE.md)
- [Testing Guide](TESTING_GUIDE.md)
- [API Documentation](backend/INTEGRATION_GUIDE.md)
- [Gamification System](GAMIFICATION_SYSTEM_GUIDE.md)
- [Monitoring & Observability](MONITORING_QUICKSTART.md)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  • Knowledge Graph Visualization (ReactFlow, Three.js)      │
│  • Study Tools & Gamification                                │
│  • PWA with Offline Support                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTPS/TLS
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                         │
│  • REST API with JWT Authentication                          │
│  • Rate Limiting & Quota Management                          │
│  • Security Headers & CSRF Protection                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│   PostgreSQL  │    │     Redis      │    │   Gemini AI  │
│   (Primary)   │    │   (Cache +     │    │     API      │
│               │    │  Rate Limit)   │    │              │
└───────────────┘    └────────────────┘    └──────────────┘
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test

# E2E tests
npm run cypress:run

# Property-based tests
pytest test_*_properties.py -v
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: Centralized JSON logging with ELK/Loki
- **Alerts**: Email, Slack, PagerDuty integration

## 🔒 Security

- JWT + API Key authentication
- Role-based access control (RBAC)
- Rate limiting (10-100 req/min based on tier)
- Quota management (token tracking & cost calculation)
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- HTTPS enforcement with automatic redirect
- Input validation & sanitization
- SQL injection & XSS prevention
- GDPR compliance (data export, deletion, audit logs)

## 🌍 Deployment

### Production Checklist
- [ ] Set up SSL/TLS certificates
- [ ] Configure environment variables
- [ ] Set up database backups
- [ ] Configure monitoring & alerting
- [ ] Set up CI/CD pipeline
- [ ] Configure CDN for static assets
- [ ] Set up log aggregation
- [ ] Configure auto-scaling

See [Production Deployment Guide](QUICK_START_PRODUCTION.md) for details.

## 📈 Performance

- **Response Time**: < 200ms (p95)
- **Uptime**: 99.9% SLA
- **Concurrent Users**: 1000+ supported
- **Cache Hit Ratio**: > 80%
- **Test Coverage**: > 80%

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for content generation
- ReactFlow for graph visualization
- Three.js for 3D visualizations
- Flask for the backend framework
- All open-source contributors

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ for learners everywhere**
