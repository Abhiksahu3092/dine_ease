# 🍽️ Restaurant Reservation AI Agent

A conversational AI agent for discovering restaurants and making reservations across major Indian cities, built with Python and Streamlit.

## 🎯 Overview

This project implements an intelligent restaurant reservation system that uses a Large Language Model (LLM) to understand user intent and interact with restaurant data naturally. The agent can search for restaurants, provide personalized recommendations, check availability, and create reservations through a friendly chat interface.

### Key Features

- **Conversational Interface**: Natural, human-like interactions powered by LLM
- **Smart Search**: Find restaurants by city, area, cuisine, price range, and features
- **Personalized Recommendations**: Get suggestions based on preferences and occasions
- **Availability Checking**: Check restaurant availability for specific dates and times
- **Reservation Management**: Create and manage restaurant bookings
- **Multi-City Support**: Covers Bangalore, Mumbai, Chennai, Hyderabad, and New Delhi

## 🏗️ Architecture

### Project Structure

```
restaurant-ai-agent/
├── app.py                 # Streamlit UI application
├── agent/
│   ├── agent.py          # Main agent loop and orchestration
│   ├── prompts.py        # System prompts and instructions
│   ├── tools.py          # Restaurant search and booking tools
│   └── schemas.py        # Pydantic models for data validation
├── data/
│   └── restaurants.json  # Static restaurant database (100 entries)
├── llm/
│   └── client.py         # LLM API client interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Component Overview

#### 1. **Agent** (`agent/agent.py`)
The core orchestrator that:
- Manages conversation history
- Coordinates between LLM and tools
- Handles tool execution and result processing
- Provides conversational flow

#### 2. **Tools** (`agent/tools.py`)
Four main capabilities:
- `search_restaurants`: Filter restaurants by criteria
- `recommend_restaurants`: Provide personalized suggestions
- `check_availability`: Verify booking slots
- `create_reservation`: Generate reservation confirmations

#### 3. **LLM Client** (`llm/client.py`)
Interface for language model integration:
- Abstracts LLM provider details
- Handles API communication
- Manages tool calling format
- **Note**: Requires implementation with your chosen LLM provider

#### 4. **Streamlit UI** (`app.py`)
User interface featuring:
- Chat-based interaction
- Conversation history
- Reset functionality
- Stats and information sidebar

## 📊 Restaurant Data

### Data Characteristics

- **Total Restaurants**: 100 (20 per city)
- **Cities Covered**: 
  - Bangalore
  - Mumbai
  - Chennai
  - Hyderabad
  - New Delhi
- **Data Source**: Curated from real, well-known restaurants
- **Status**: **STATIC** - not real-time or live data

### Restaurant Attributes

Each restaurant entry includes:
- `id`: Unique identifier
- `name`: Restaurant name (real establishments)
- `city`: Location city
- `area`: Neighborhood/locality (real areas)
- `cuisine`: Type(s) of food served (1-3 types)
- `capacity`: Estimated seating (30-120)
- `price_range`: Budget indicator (₹, ₹₹, ₹₹₹)
- `rating`: Approximate rating (3.5-4.8)
- `features`: Notable characteristics (e.g., Rooftop, Fine Dining)
- `opening_hours`: Operating hours (generic)

### ⚠️ Data Disclaimer

**IMPORTANT**: While restaurant names and locations are based on real establishments, all other data (ratings, capacity, hours, etc.) is illustrative and intended for demonstration purposes only. This is NOT real-time data and should not be used for actual restaurant information or bookings.

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenRouter API key (get it at https://openrouter.ai/keys)

### Installation

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd restaurant-ai-agent
   ```

3. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   
   Copy the example environment file and add your API key:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   ```
   
   Get your free API key at: https://openrouter.ai/keys
   
   **Note**: The `.env` file is already configured and ready to use. The project uses OpenRouter API for LLM access with the free Qwen model by default

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 🎮 Usage Examples

### Searching for Restaurants

```
User: I'm looking for Italian restaurants in Bangalore
Agent: [Searches database and presents options]
```

### Getting Recommendations

```
User: Can you recommend a romantic place in Mumbai for an anniversary?
Agent: [Filters for fine dining, considers occasion, provides curated suggestions]
```

### Making a Reservation

```
User: Check if Toit in Bangalore is available on December 25th at 7 PM for 4 people
Agent: [Checks availability, confirms or suggests alternatives]
User: Please book it for me
Agent: [Requests customer details and creates reservation]
```

## 🔧 Development Notes

### Design Constraints

This project intentionally **AVOIDS**:
- ❌ LangChain, LlamaIndex, or similar frameworks
- ❌ Real-time API calls to external services
- ❌ Live restaurant data or pricing
- ❌ Keyword-based routing (LLM decides intent)

### TODO Items

The codebase includes several `TODO` markers for areas requiring implementation or enhancement:

**High Priority**:
- [ ] Implement actual LLM integration in `llm/client.py`
- [ ] Complete agent loop with tool calling in `agent/agent.py`
- [ ] Add proper input validation throughout

**Medium Priority**:
- [ ] Enhanced recommendation algorithm
- [ ] Better availability simulation logic
- [ ] Date/time validation
- [ ] Error handling and retry logic

**Nice to Have**:
- [ ] Conversation export
- [ ] Multi-language support
- [ ] Advanced filtering options
- [ ] User preference memory

### Extending the Project

#### Adding More Restaurants

Edit `data/restaurants.json` to add new entries following the existing schema.

#### Adding New Tools

1. Define input/output schemas in `agent/schemas.py`
2. Implement tool function in `agent/tools.py`
3. Add to `TOOLS` and `TOOL_DESCRIPTIONS` dictionaries
4. Update system prompt to include new capability

#### Changing LLM Provider

Modify `llm/client.py` to use your preferred provider's API. The interface is designed to be provider-agnostic.

## 📝 System Behavior

### Greeting

The agent **proactively greets users** when the conversation starts, introducing its capabilities before any user input.

### Tone and Style

- Friendly and professional
- Natural, conversational language
- Patient with clarifying questions
- Transparent about limitations
- No fabrication of data

### Decision Making

The LLM decides:
- When to call which tools
- What information to request from users
- How to present results
- When to proceed with reservations

**Not** hard-coded keyword matching or rule-based flows.

## 🔒 Limitations and Disclaimers

1. **Static Data**: All restaurant information is static and illustrative
2. **No Real Bookings**: Reservations are simulated; no actual bookings are made
3. **No Live Integration**: No connections to real restaurant systems
4. **No Real-time Information**: Availability, pricing, and hours are simulated
5. **Demonstration Purpose**: This is a prototype/learning project

## 📄 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

This is a scaffold/template project. Feel free to:
- Implement the TODO items
- Enhance the UI
- Improve the conversation flow
- Add new features
- Optimize the code

## 📧 Support

For issues or questions about the codebase, refer to the inline comments and TODO markers for guidance on implementation.

---

**Happy Building! 🚀**
