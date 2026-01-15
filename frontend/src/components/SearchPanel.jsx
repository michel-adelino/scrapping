import { useState, useEffect, useRef } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const LAWN_CLUB_TIMES = [
  "6:00 AM",
  "6:15 AM",
  "6:30 AM",
  "6:45 AM",
  "7:00 AM",
  "7:15 AM",
  "7:30 AM",
  "7:45 AM",
  // ... add all times (96 total)
];

const LAWN_CLUB_DURATIONS = [
  "1 hr",
  "1 hr 30 min",
  "2 hr",
  "2 hr 30 min",
  "3 hr",
];

const VENUE_INFO = {
  swingers_nyc: {
    name: "Swingers (NYC)",
    description:
      "Golf club and restaurant offering crazy golf, cocktails, and street food. Can scrape multiple dates if no specific date is selected.",
  },
  swingers_london: {
    name: "Swingers (London)",
    description:
      "Golf club and restaurant offering crazy golf, cocktails, and street food. Can scrape multiple dates if no specific date is selected.",
  },
  electric_shuffle_nyc: {
    name: "Electric Shuffle (NYC)",
    description:
      "Shuffleboard bar and restaurant. Requires a specific target date.",
  },
  electric_shuffle_london: {
    name: "Electric Shuffle (London)",
    description:
      "Shuffleboard bar and restaurant. Requires a specific target date.",
  },
  lawn_club_nyc: {
    name: "Lawn Club NYC",
    description: "Lawn games and activities. Requires a specific target date.",
  },
  spin_nyc: {
    name: "SPIN (NYC)",
    description:
      "Ping pong bar and restaurant. Requires a specific target date.",
  },
  five_iron_golf_nyc: {
    name: "Five Iron Golf (NYC)",
    description:
      "Indoor golf and entertainment. Requires a specific target date.",
  },
  lucky_strike_nyc: {
    name: "Lucky Strike (NYC)",
    description:
      "Bowling alley and entertainment. Requires a specific target date.",
  },
  easybowl_nyc: {
    name: "Easybowl (NYC)",
    description: "Bowling and entertainment. Requires a specific target date.",
  },
  fair_game_canary_wharf: {
    name: "Fair Game (Canary Wharf)",
    description: "Games and entertainment. Requires a specific target date.",
  },
  fair_game_city: {
    name: "Fair Game (City)",
    description: "Games and entertainment. Requires a specific target date.",
  },
  clays_bar: {
    name: "Clays Bar",
    description: "Clay shooting and bar. Requires a specific target date.",
  },
  puttshack: {
    name: "Puttshack",
    description:
      "Mini golf and entertainment. Requires a specific target date.",
  },
  flight_club_darts: {
    name: "Flight Club Darts (Bloomsbury)",
    description: "Darts and entertainment. Requires a specific target date.",
  },
  flight_club_darts_angel: {
    name: "Flight Club Darts (Angel)",
    description: "Darts and entertainment. Requires a specific target date.",
  },
  flight_club_darts_shoreditch: {
    name: "Flight Club Darts (Shoreditch)",
    description: "Darts and entertainment. Requires a specific target date.",
  },
  flight_club_darts_victoria: {
    name: "Flight Club Darts (Victoria)",
    description: "Darts and entertainment. Requires a specific target date.",
  },
  f1_arcade: {
    name: "F1 Arcade",
    description: "F1 racing simulation. Requires a specific target date.",
  },
  all_new_york: {
    name: "All New York",
    description: "Search all NYC venues at once.",
  },
  all_london: {
    name: "All London",
    description: "Search all London venues at once.",
  },
};

const VENUE_NAME_MAP = {
  swingers_nyc: "Swingers (NYC)",
  swingers_london: "Swingers (London)",
  electric_shuffle_nyc: "Electric Shuffle (NYC)",
  electric_shuffle_london: "Electric Shuffle (London)",
  lawn_club_nyc: "Lawn Club NYC",
  spin_nyc: "SPIN (NYC)",
  five_iron_golf_nyc: "Five Iron Golf (NYC)",
  lucky_strike_nyc: "Lucky Strike (NYC)",
  easybowl_nyc: "Easybowl (NYC)",
  fair_game_canary_wharf: "Fair Game (Canary Wharf)",
  fair_game_city: "Fair Game (City)",
  clays_bar: "Clays Bar",
  puttshack: "Puttshack",
  flight_club_darts: "Flight Club Darts (Bloomsbury)",
  flight_club_darts_angel: "Flight Club Darts (Angel)",
  flight_club_darts_shoreditch: "Flight Club Darts (Shoreditch)",
  flight_club_darts_victoria: "Flight Club Darts (Victoria)",
  f1_arcade: "F1 Arcade",
};

function SearchPanel({ onSearch, onClear, isLoading = false }) {
  const [location, setLocation] = useState("all_london"); // 'all_new_york' or 'all_london'
  const [guests, setGuests] = useState(2);
  const [targetDate, setTargetDate] = useState(null); // Date object or null for DatePicker
  const [dateSelectionMode, setDateSelectionMode] = useState("dates"); // "dates", "months", "flexible"
  const [flexibleDays, setFlexibleDays] = useState(0); // 0 for exact, 1, 2, 3, 7, 14 for flexible
  const [dateRangeStart, setDateRangeStart] = useState(null); // Start date for Flexible mode
  const [dateRangeEnd, setDateRangeEnd] = useState(null); // End date for Flexible mode
  const [isCalendarOpen, setIsCalendarOpen] = useState(false); // Track if calendar should be open
  const [activeSection, setActiveSection] = useState(null); // Track which section overlay is open: "where", "when", "who", or null
  const datePickerRef = useRef(null); // Ref for Dates mode DatePicker
  const flexibleDatePickerRef = useRef(null); // Ref for Flexible mode DatePicker
  const whereSectionRef = useRef(null); // Ref for Where section (for overlay positioning)
  const whenSectionRef = useRef(null); // Ref for When section (for overlay positioning)
  const whoSectionRef = useRef(null); // Ref for Who section (for overlay positioning)
  const [lawnClubOption, setLawnClubOption] = useState(
    "Curling Lawns & Cabins"
  );
  const [lawnClubTime, setLawnClubTime] = useState("");
  const [lawnClubDuration, setLawnClubDuration] = useState("");
  const [spinTime, setSpinTime] = useState("");
  const [claysLocation, setClaysLocation] = useState("Canary Wharf");
  const [puttshackLocation, setPuttshackLocation] = useState("Bank");
  const [f1Experience, setF1Experience] = useState("Team Racing");

  const venueInfo = VENUE_INFO[location] || VENUE_INFO["all_new_york"];
  const requiresDate = false; // Always false since we're only showing all_new_york or all_london

  const getDefaultDateFilters = () => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    return {
      date_from: today.toISOString().split("T")[0],
      date_to: tomorrow.toISOString().split("T")[0],
    };
  };

  const calculateDateRange = (selectedDate, flexibleDays) => {
    if (!selectedDate) return null;
    
    const startDate = new Date(selectedDate);
    startDate.setDate(startDate.getDate() - flexibleDays);
    
    const endDate = new Date(selectedDate);
    endDate.setDate(endDate.getDate() + flexibleDays);
    
    return {
      date_from: startDate.toISOString().split("T")[0],
      date_to: endDate.toISOString().split("T")[0]
    };
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    const filters = {};

    // For "All New York" and "All London", don't apply date filters by default
    // User can still specify a date if they want
    const isMultiVenue = true; // Always true since we only have all_new_york or all_london

    // Handle date filters based on selection mode
    if (dateSelectionMode === "dates") {
      // Dates mode: single date with flexible days
      if (targetDate) {
        const dateRange = calculateDateRange(targetDate, flexibleDays);
        if (dateRange) {
          filters.date_from = dateRange.date_from;
          filters.date_to = dateRange.date_to;
        }
      }
    } else if (dateSelectionMode === "months") {
      // Months mode: auto 30-day range from today
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const endDate = new Date(today);
      endDate.setDate(endDate.getDate() + 30);
      filters.date_from = today.toISOString().split("T")[0];
      filters.date_to = endDate.toISOString().split("T")[0];
    } else if (dateSelectionMode === "flexible") {
      // Flexible mode: use selected date range
      if (dateRangeStart && dateRangeEnd) {
        filters.date_from = dateRangeStart.toISOString().split("T")[0];
        filters.date_to = dateRangeEnd.toISOString().split("T")[0];
      }
    }
    // Otherwise, no date filter - show all available slots

    // Add venue/city filter
    if (location === "all_new_york") {
      filters.city = "NYC";
      delete filters.venue_name;
    } else if (location === "all_london") {
      filters.city = "London";
      delete filters.venue_name;
    }

    // Add guests filter
    filters.guests = guests;

    onSearch(filters, guests, isMultiVenue);
  };

  const handleToday = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    setTargetDate(today);
    setDateSelectionMode("dates");
  };

  const handleTomorrow = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    setTargetDate(tomorrow);
    setDateSelectionMode("dates");
  };

  const handleFlexibleRangeAdjust = (days) => {
    if (dateRangeStart && dateRangeEnd) {
      // Expand/contract existing range
      const newStart = new Date(dateRangeStart);
      newStart.setDate(newStart.getDate() - days);
      
      const newEnd = new Date(dateRangeEnd);
      newEnd.setDate(newEnd.getDate() + days);
      
      setDateRangeStart(newStart);
      setDateRangeEnd(newEnd);
    } else if (targetDate) {
      // If no range but single date selected, create range around it
      const start = new Date(targetDate);
      start.setDate(start.getDate() - days);
      start.setHours(0, 0, 0, 0);
      const end = new Date(targetDate);
      end.setDate(end.getDate() + days);
      end.setHours(0, 0, 0, 0);
      setDateRangeStart(start);
      setDateRangeEnd(end);
    } else {
      // If no date selected, create range around today
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const start = new Date(today);
      start.setDate(start.getDate() - days);
      const end = new Date(today);
      end.setDate(end.getDate() + days);
      setDateRangeStart(start);
      setDateRangeEnd(end);
    }
  };

  // Handle section click to toggle overlay
  const handleSectionClick = (section) => {
    setActiveSection(activeSection === section ? null : section);
  };

  // Handle location selection
  const handleLocationSelect = (loc) => {
    setLocation(loc);
    setActiveSection(null); // Close overlay after selection
  };

  // Get display text for Where section
  const getWhereDisplayText = () => {
    if (location === "all_new_york") return "New York";
    if (location === "all_london") return "London";
    return "Search destinations";
  };

  // Get display text for When section
  const getWhenDisplayText = () => {
    if (dateSelectionMode === "months") {
      return "Next 30 days";
    }
    if (dateSelectionMode === "flexible" && dateRangeStart && dateRangeEnd) {
      const startStr = dateRangeStart.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      const endStr = dateRangeEnd.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      return `${startStr} - ${endStr}`;
    }
    if (dateSelectionMode === "dates" && targetDate) {
      return targetDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    }
    return "Add dates";
  };

  // Get display text for Who section
  const getWhoDisplayText = () => {
    if (guests === 0) return "Add guests";
    if (guests === 1) return "1 guest";
    return `${guests} guests`;
  };

  // Click outside detection to close overlays
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (activeSection) {
        // Check if click is outside the section and overlay
        const isClickInSection = e.target.closest('.search-bar-section');
        const isClickInOverlay = e.target.closest('.search-overlay');
        const isClickInCalendar = e.target.closest('.react-datepicker');
        
        if (!isClickInSection && !isClickInOverlay && !isClickInCalendar) {
          setActiveSection(null);
        }
      }
    };

    if (activeSection) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [activeSection]);

  // Keep calendar open when switching between dates and flexible modes
  const previousModeRef = useRef(dateSelectionMode);
  const shouldKeepOpenRef = useRef(false);
  
  useEffect(() => {
    const previousMode = previousModeRef.current;
    
    // If switching between dates and flexible (and calendar was open), reopen it
    if (shouldKeepOpenRef.current && 
        ((previousMode === "dates" && dateSelectionMode === "flexible") ||
         (previousMode === "flexible" && dateSelectionMode === "dates"))) {
      // Wait for React to render the new DatePicker, then open it by clicking the input
      setTimeout(() => {
        // Find the input element - react-datepicker renders it with the id we provide
        const inputId = dateSelectionMode === "dates" ? "targetDate" : "dateRange";
        const input = document.getElementById(inputId);
        
        if (input) {
          // Trigger click to open the calendar
          input.focus();
          input.click();
          shouldKeepOpenRef.current = false; // Reset flag
        } else {
          // Fallback: try to find input in the wrapper
          const wrapper = document.querySelector(`.datepicker-wrapper`);
          const fallbackInput = wrapper?.querySelector('input[type="text"]');
          if (fallbackInput) {
            fallbackInput.focus();
            fallbackInput.click();
            shouldKeepOpenRef.current = false;
          }
        }
      }, 100);
    } else {
      // Reset flag if not switching between dates/flexible
      shouldKeepOpenRef.current = false;
    }
    
    previousModeRef.current = dateSelectionMode;
  }, [dateSelectionMode]);

  // Inject buttons into calendar popup when it opens
  useEffect(() => {
    // Use event delegation for mode selector buttons
    const handleModeSelectorClick = (e) => {
      const btn = e.target.closest('.segmented-btn[data-mode]');
      if (!btn) return;
      
      e.stopPropagation();
      e.preventDefault();
      
      const mode = btn.getAttribute('data-mode');
      const wasCalendarOpen = document.querySelector('.react-datepicker') !== null;
      
      if (mode === "months") {
        // For months mode, close the calendar
        setIsCalendarOpen(false);
        shouldKeepOpenRef.current = false;
        setDateSelectionMode(mode);
      } else {
        // For dates/flexible, keep calendar open if it was open
        if (wasCalendarOpen) {
          shouldKeepOpenRef.current = true;
          setIsCalendarOpen(true);
        }
        setDateSelectionMode(mode);
      }
    };

    const injectButtons = () => {
      const calendar = document.querySelector('.react-datepicker');
      if (!calendar) return;

      // Check if mode selector already exists - if so, just update active state
      let existingModeSelector = calendar.querySelector('.calendar-mode-selector');
      
      if (!existingModeSelector) {
        // Create mode selector (Dates/Months/Flexible) at the top
        existingModeSelector = document.createElement('div');
        existingModeSelector.className = 'calendar-mode-selector';
        existingModeSelector.innerHTML = `
          <div class="segmented-control calendar-segmented-control">
            <button type="button" class="segmented-btn" data-mode="dates">Dates</button>
            <button type="button" class="segmented-btn" data-mode="months">Months</button>
            <button type="button" class="segmented-btn" data-mode="flexible">Flexible</button>
          </div>
        `;

        // Insert mode selector at the beginning of calendar (before month containers)
        const firstChild = calendar.firstChild;
        if (firstChild) {
          calendar.insertBefore(existingModeSelector, firstChild);
        } else {
          calendar.appendChild(existingModeSelector);
        }
        
        // Add event listener to the mode selector using delegation
        // Only attach once when the selector is created
        existingModeSelector.addEventListener('click', handleModeSelectorClick, true);
      }
      
      // Update active state without removing/recreating buttons
      existingModeSelector.querySelectorAll('.segmented-btn').forEach(btn => {
        const btnMode = btn.getAttribute('data-mode');
        if (btnMode === dateSelectionMode) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });

      // Remove existing quick/flexible buttons if any
      const existingQuick = calendar.querySelector('.calendar-quick-buttons');
      const existingFlexible = calendar.querySelector('.calendar-flexible-buttons');
      if (existingQuick) existingQuick.remove();
      if (existingFlexible) existingFlexible.remove();

      // Create quick buttons (Today/Tomorrow) for Dates mode
      if (dateSelectionMode === "dates") {
        const quickButtons = document.createElement('div');
        quickButtons.className = 'calendar-quick-buttons';
        quickButtons.innerHTML = `
          <button type="button" class="calendar-quick-btn" data-action="today">Today</button>
          <button type="button" class="calendar-quick-btn" data-action="tomorrow">Tomorrow</button>
        `;
        calendar.appendChild(quickButtons);

        // Add event listeners for quick buttons
        const todayBtn = quickButtons.querySelector('[data-action="today"]');
        const tomorrowBtn = quickButtons.querySelector('[data-action="tomorrow"]');
        
        if (todayBtn) {
          todayBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            setTargetDate(today);
            setDateSelectionMode("dates");
          });
        }
        
        if (tomorrowBtn) {
          tomorrowBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(0, 0, 0, 0);
            setTargetDate(tomorrow);
            setDateSelectionMode("dates");
          });
        }
      }

      // Create flexible buttons for Flexible mode (for expanding/contracting range)
      if (dateSelectionMode === "flexible") {
        const flexibleButtons = document.createElement('div');
        flexibleButtons.className = 'calendar-flexible-buttons';
        const daysOptions = [1, 2, 3, 7, 14];
        const labels = ['±1', '±2', '±3', '±7', '±14'];
        flexibleButtons.innerHTML = daysOptions.map((days, idx) => 
          `<button type="button" class="calendar-flexible-btn" data-days="${days}">${labels[idx]}</button>`
        ).join('');
        calendar.appendChild(flexibleButtons);

        // Add event listeners for flexible buttons in Flexible mode
        flexibleButtons.querySelectorAll('.calendar-flexible-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const days = parseInt(btn.getAttribute('data-days') || '0');
            handleFlexibleRangeAdjust(days);
          });
        });
      }
    };

    // Use MutationObserver to detect when calendar opens
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length) {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1 && (node.classList?.contains('react-datepicker') || node.querySelector?.('.react-datepicker'))) {
              setTimeout(injectButtons, 50);
            }
          });
        }
      });
    });

    // Observe the document body for calendar popup
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Also check periodically when calendar might be open
    const interval = setInterval(() => {
      if (document.querySelector('.react-datepicker')) {
        injectButtons();
      }
    }, 200);

    return () => {
      observer.disconnect();
      clearInterval(interval);
    };
  }, [flexibleDays, dateSelectionMode, dateRangeStart, dateRangeEnd, targetDate]);

  // Trigger button injection when When overlay opens
  useEffect(() => {
    if (activeSection === "when") {
      // Wait for calendar to render, then inject buttons
      const checkAndInject = () => {
        const calendar = document.querySelector('.react-datepicker');
        if (calendar) {
          // Use the existing injectButtons function logic
          const injectButtons = () => {
            const calendar = document.querySelector('.react-datepicker');
            if (!calendar) return;

            // Check if mode selector already exists - if so, just update active state
            let existingModeSelector = calendar.querySelector('.calendar-mode-selector');
            
            if (!existingModeSelector) {
              // Create mode selector (Dates/Months/Flexible) at the top
              existingModeSelector = document.createElement('div');
              existingModeSelector.className = 'calendar-mode-selector';
              existingModeSelector.innerHTML = `
                <div class="segmented-control calendar-segmented-control">
                  <button type="button" class="segmented-btn" data-mode="dates">Dates</button>
                  <button type="button" class="segmented-btn" data-mode="months">Months</button>
                  <button type="button" class="segmented-btn" data-mode="flexible">Flexible</button>
                </div>
              `;

              // Insert mode selector at the beginning of calendar (before month containers)
              const firstChild = calendar.firstChild;
              if (firstChild) {
                calendar.insertBefore(existingModeSelector, firstChild);
              } else {
                calendar.appendChild(existingModeSelector);
              }
              
              // Add event listener for mode selector buttons
              existingModeSelector.querySelectorAll('.segmented-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  const mode = btn.getAttribute('data-mode');
                  const wasCalendarOpen = document.querySelector('.react-datepicker') !== null;
                  
                  if (mode === "months") {
                    setIsCalendarOpen(false);
                    shouldKeepOpenRef.current = false;
                    setDateSelectionMode(mode);
                  } else {
                    if (wasCalendarOpen) {
                      shouldKeepOpenRef.current = true;
                      setIsCalendarOpen(true);
                    }
                    setDateSelectionMode(mode);
                  }
                  
                  // Update active state
                  existingModeSelector.querySelectorAll('.segmented-btn').forEach(b => b.classList.remove('active'));
                  btn.classList.add('active');
                });
              });
            }
            
            // Update active state
            existingModeSelector.querySelectorAll('.segmented-btn').forEach(btn => {
              const btnMode = btn.getAttribute('data-mode');
              if (btnMode === dateSelectionMode) {
                btn.classList.add('active');
              } else {
                btn.classList.remove('active');
              }
            });

            // Remove existing quick/flexible buttons if any
            const existingQuick = calendar.querySelector('.calendar-quick-buttons');
            const existingFlexible = calendar.querySelector('.calendar-flexible-buttons');
            if (existingQuick) existingQuick.remove();
            if (existingFlexible) existingFlexible.remove();

            // Create quick buttons (Today/Tomorrow) for Dates mode
            if (dateSelectionMode === "dates") {
              const quickButtons = document.createElement('div');
              quickButtons.className = 'calendar-quick-buttons';
              quickButtons.innerHTML = `
                <button type="button" class="calendar-quick-btn" data-action="today">Today</button>
                <button type="button" class="calendar-quick-btn" data-action="tomorrow">Tomorrow</button>
              `;
              calendar.appendChild(quickButtons);

              // Add event listeners for quick buttons
              const todayBtn = quickButtons.querySelector('[data-action="today"]');
              const tomorrowBtn = quickButtons.querySelector('[data-action="tomorrow"]');
              
              if (todayBtn) {
                todayBtn.addEventListener('click', (e) => {
                  e.stopPropagation();
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);
                  setTargetDate(today);
                  setDateSelectionMode("dates");
                });
              }
              
              if (tomorrowBtn) {
                tomorrowBtn.addEventListener('click', (e) => {
                  e.stopPropagation();
                  const tomorrow = new Date();
                  tomorrow.setDate(tomorrow.getDate() + 1);
                  tomorrow.setHours(0, 0, 0, 0);
                  setTargetDate(tomorrow);
                  setDateSelectionMode("dates");
                });
              }
            }

            // Create flexible buttons for Flexible mode
            if (dateSelectionMode === "flexible") {
              const flexibleButtons = document.createElement('div');
              flexibleButtons.className = 'calendar-flexible-buttons';
              const daysOptions = [1, 2, 3, 7, 14];
              const labels = ['±1', '±2', '±3', '±7', '±14'];
              flexibleButtons.innerHTML = daysOptions.map((days, idx) => 
                `<button type="button" class="calendar-flexible-btn" data-days="${days}">${labels[idx]}</button>`
              ).join('');
              calendar.appendChild(flexibleButtons);

              // Add event listeners for flexible buttons
              flexibleButtons.querySelectorAll('.calendar-flexible-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                  e.stopPropagation();
                  const days = parseInt(btn.getAttribute('data-days') || '0');
                  handleFlexibleRangeAdjust(days);
                });
              });
            }
          };

          injectButtons();
        }
      };

      // Try immediately, then with delays to ensure calendar is rendered
      checkAndInject();
      const timeout1 = setTimeout(checkAndInject, 100);
      const timeout2 = setTimeout(checkAndInject, 300);
      const timeout3 = setTimeout(checkAndInject, 500);

      return () => {
        clearTimeout(timeout1);
        clearTimeout(timeout2);
        clearTimeout(timeout3);
      };
    }
  }, [activeSection, dateSelectionMode, flexibleDays, dateRangeStart, dateRangeEnd, targetDate]);

  return (
    <div className="control-panel">
      <form onSubmit={handleSearch}>
        <div className="airbnb-search-bar">
          {/* Where Section */}
          <div 
            ref={whereSectionRef}
            className={`search-bar-section ${activeSection === "where" ? "active" : ""}`}
            onClick={() => handleSectionClick("where")}
          >
            <div className="search-bar-label">Where</div>
            <div className="search-bar-value">{getWhereDisplayText()}</div>
            
            {activeSection === "where" && (
              <div className="search-overlay search-overlay-where">
                <button
                  type="button"
                  className={`location-option ${location === "all_london" ? "active" : ""}`}
                  onClick={() => handleLocationSelect("all_london")}
                >
                  London
                </button>
                <button
                  type="button"
                  className={`location-option ${location === "all_new_york" ? "active" : ""}`}
                  onClick={() => handleLocationSelect("all_new_york")}
                >
                  New York
                </button>
              </div>
            )}
          </div>

          <div className="search-bar-separator"></div>

          {/* When Section */}
          <div 
            ref={whenSectionRef}
            className={`search-bar-section ${activeSection === "when" ? "active" : ""}`}
            onClick={(e) => {
              e.stopPropagation();
              handleSectionClick("when");
            }}
          >
            <div className="search-bar-label">When</div>
            <div className="search-bar-value">{getWhenDisplayText()}</div>
            
            {activeSection === "when" && (
              <div className="search-overlay search-overlay-when" onClick={(e) => e.stopPropagation()}>
                <div className="date-selection-section">
              {dateSelectionMode === "dates" && (
                <div className="calendar-container">
                  <div className="input-field">
                    <span className="icon">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M8 2v4" />
                        <path d="M16 2v4" />
                        <rect width="18" height="18" x="3" y="4" rx="2" />
                        <path d="M3 10h18" />
                        <path d="M8 14h.01" />
                        <path d="M12 14h.01" />
                        <path d="M16 14h.01" />
                        <path d="M8 18h.01" />
                        <path d="M12 18h.01" />
                        <path d="M16 18h.01" />
                      </svg>
                    </span>
                    <DatePicker
                      ref={datePickerRef}
                      id="targetDate"
                      selected={targetDate}
                      onChange={(date) => setTargetDate(date)}
                      onCalendarOpen={() => setIsCalendarOpen(true)}
                      onCalendarClose={() => setIsCalendarOpen(false)}
                      open={activeSection === "when"}
                      withPortal={false}
                      dateFormat="MMM dd, yyyy"
                      placeholderText="Select a date"
                      minDate={new Date()}
                      monthsShown={1}
                      className="form-control datepicker-input"
                      wrapperClassName="datepicker-wrapper"
                      calendarClassName="modern-calendar"
                    />
                  </div>
                </div>
              )}
              {dateSelectionMode === "flexible" && (
                <div className="calendar-container">
                  <div className="input-field">
                    <span className="icon">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M8 2v4" />
                        <path d="M16 2v4" />
                        <rect width="18" height="18" x="3" y="4" rx="2" />
                        <path d="M3 10h18" />
                        <path d="M8 14h.01" />
                        <path d="M12 14h.01" />
                        <path d="M16 14h.01" />
                        <path d="M8 18h.01" />
                        <path d="M12 18h.01" />
                        <path d="M16 18h.01" />
                      </svg>
                    </span>
                    <DatePicker
                      ref={flexibleDatePickerRef}
                      id="dateRange"
                      selectsRange={true}
                      startDate={dateRangeStart}
                      endDate={dateRangeEnd}
                      onChange={(dates) => {
                        const [start, end] = dates;
                        setDateRangeStart(start);
                        setDateRangeEnd(end);
                      }}
                      onCalendarOpen={() => setIsCalendarOpen(true)}
                      onCalendarClose={() => setIsCalendarOpen(false)}
                      open={activeSection === "when"}
                      withPortal={false}
                      dateFormat="MMM dd, yyyy"
                      placeholderText="Select date range"
                      minDate={new Date()}
                      monthsShown={1}
                      className="form-control datepicker-input"
                      wrapperClassName="datepicker-wrapper"
                      calendarClassName="modern-calendar"
                    />
                  </div>
                </div>
              )}
              {dateSelectionMode === "months" && (
                <div className="calendar-container">
                  <div className="input-field">
                    <span className="icon">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M8 2v4" />
                        <path d="M16 2v4" />
                        <rect width="18" height="18" x="3" y="4" rx="2" />
                        <path d="M3 10h18" />
                        <path d="M8 14h.01" />
                        <path d="M12 14h.01" />
                        <path d="M16 14h.01" />
                        <path d="M8 18h.01" />
                        <path d="M12 18h.01" />
                        <path d="M16 18h.01" />
                      </svg>
                    </span>
                    <DatePicker
                      ref={datePickerRef}
                      id="monthsDatePicker"
                      selected={null}
                      onChange={() => {}}
                      onCalendarOpen={() => {
                        setIsCalendarOpen(true);
                        // Switch to dates mode when calendar opens, with a small delay to ensure calendar stays open
                        setTimeout(() => {
                          setDateSelectionMode("dates");
                        }, 10);
                      }}
                      onCalendarClose={() => setIsCalendarOpen(false)}
                      open={activeSection === "when"}
                      withPortal={false}
                      dateFormat="MMM dd, yyyy"
                      placeholderText="Next 30 days"
                      minDate={new Date()}
                      monthsShown={1}
                      className="form-control datepicker-input"
                      wrapperClassName="datepicker-wrapper"
                      calendarClassName="modern-calendar"
                    />
                  </div>
                </div>
              )}
                </div>
              </div>
            )}
          </div>

          <div className="search-bar-separator"></div>

          {/* Who Section */}
          <div 
            ref={whoSectionRef}
            className={`search-bar-section ${activeSection === "who" ? "active" : ""}`}
            onClick={() => handleSectionClick("who")}
          >
            <div className="search-bar-label">Who</div>
            <div className="search-bar-value">{getWhoDisplayText()}</div>
            
            {activeSection === "who" && (
              <div className="search-overlay search-overlay-who">
                <div className="guest-selector-overlay">
                  <div className="guest-picker">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setGuests(Math.max(1, guests - 1));
                      }}
                      aria-label="Decrease guests"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M5 12h14" />
                      </svg>
                    </button>
                    <input
                      type="number"
                      id="guests"
                      min="1"
                      max="8"
                      value={guests}
                      readOnly
                      required
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setGuests(Math.min(8, guests + 1));
                      }}
                      aria-label="Increase guests"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M5 12h14" />
                        <path d="M12 5v14" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Search Button */}
          <button 
            type="submit" 
            className="search-bar-button" 
            disabled={isLoading}
            onClick={(e) => {
              e.stopPropagation();
              handleSearch(e);
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m21 21-4.34-4.34" />
              <circle cx="11" cy="11" r="8" />
            </svg>
          </button>
        </div>


        <div className="options-grid">
          {false && location === "lawn_club_nyc" && (
            <>
              <div className="option-card">
                <label htmlFor="lawnClubOption">Lawn Club Experience</label>
                <select
                  id="lawnClubOption"
                  className="form-control"
                  value={lawnClubOption}
                  onChange={(e) => setLawnClubOption(e.target.value)}
                >
                  <option value="Curling Lawns & Cabins">
                    Curling Lawns & Cabins
                  </option>
                  <option value="Indoor Gaming Lawns">
                    Indoor Gaming Lawns
                  </option>
                  <option value="Croquet Lawns">Croquet Lawns</option>
                </select>
              </div>
            </>
          )}

          {false && location === "clays_bar" && (
            <div className="option-card">
              <label htmlFor="claysLocation">Clays Bar Location</label>
              <select
                id="claysLocation"
                className="form-control"
                value={claysLocation}
                onChange={(e) => setClaysLocation(e.target.value)}
              >
                <option value="Canary Wharf">Canary Wharf</option>
                <option value="The City">The City</option>
                <option value="Birmingham">Birmingham</option>
                <option value="Soho">Soho</option>
              </select>
            </div>
          )}

          {false && location === "puttshack" && (
            <div className="option-card">
              <label htmlFor="puttshackLocation">Puttshack Location</label>
              <select
                id="puttshackLocation"
                className="form-control"
                value={puttshackLocation}
                onChange={(e) => setPuttshackLocation(e.target.value)}
              >
                <option value="Bank">Bank</option>
                <option value="Lakeside">Lakeside</option>
                <option value="White City">White City</option>
                <option value="Watford">Watford</option>
              </select>
            </div>
          )}

          {false && location === "f1_arcade" && (
            <div className="option-card">
              <label htmlFor="f1Experience">F1 Arcade Experience</label>
              <select
                id="f1Experience"
                className="form-control"
                value={f1Experience}
                onChange={(e) => setF1Experience(e.target.value)}
              >
                {guests < 4 ? (
                  <option value="Head to Head">Head to Head</option>
                ) : (
                  <>
                    <option value="Team Racing">Team Racing</option>
                    <option value="Christmas Racing">Christmas Racing</option>
                  </>
                )}
              </select>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

export default SearchPanel;
