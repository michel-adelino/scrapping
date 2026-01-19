// Venue metadata extracted from CSV files
// Maps venue names (as stored in database) to neighborhood, description, location, and activities

// Helper function to normalize venue names for matching
const normalizeVenueName = (name) => {
  return name.toLowerCase().replace(/\s+/g, ' ').trim();
};

// Helper function to extract base venue name (without location)
const getBaseVenueName = (venueName) => {
  // Remove patterns like "(NYC - Location)", "(London)", "(Location)"
  return venueName.replace(/\s*\([^)]*\)\s*$/, '').trim();
};

// Helper function to extract location from venue name
const extractLocation = (venueName) => {
  const match = venueName.match(/\(([^)]+)\)/);
  if (match) {
    const locationPart = match[1];
    // Remove city prefix like "NYC - " or "London - "
    return locationPart.replace(/^(NYC|London)\s*-\s*/i, '').trim();
  }
  return null;
};

// NYC venues metadata
const nycVenues = {
  'Swingers (NYC)': {
    venueName: 'Swingers',
    location: 'Nomad',
    neighborhood: 'Midtown',
    description: 'Adults-only mini-golf paired with street-food style dining and bar service',
    city: 'NYC'
  },
  'Electric Shuffle (NYC)': {
    venueName: 'Electric Shuffle',
    location: 'Nomad',
    neighborhood: 'Midtown',
    description: 'Technology-enabled shuffleboard with TV screens and restaurant service',
    city: 'NYC'
  },
  'Puttery (NYC)': {
    venueName: 'Puttery',
    location: 'Meatpacking',
    neighborhood: 'Downtown',
    description: '21+ indoor mini-golf positioned around cocktails and full-service dining.',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - FiDi)': {
    venueName: 'Five Iron Golf',
    location: 'Financial District',
    neighborhood: 'Downtown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Flatiron)': {
    venueName: 'Five Iron Golf',
    location: 'Flatiron',
    neighborhood: 'Midtown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Grand Central)': {
    venueName: 'Five Iron Golf',
    location: 'Midtown East',
    neighborhood: 'Midtown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Herald Square)': {
    venueName: 'Five Iron Golf',
    location: 'Herald Square',
    neighborhood: 'Midtown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Long Island City)': {
    venueName: 'Five Iron Golf',
    location: 'Long Island City',
    neighborhood: 'Brooklyn/Queens',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Upper East Side)': {
    venueName: 'Five Iron Golf',
    location: 'Upper East Side',
    neighborhood: 'Uptown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'Five Iron Golf (NYC - Rockefeller Center)': {
    venueName: 'Five Iron Golf',
    location: 'Rockefeller Center',
    neighborhood: 'Midtown',
    description: 'Indoor golf simulator venues offering practice, leagues, and bar service',
    city: 'NYC'
  },
  'SPIN (NYC - Flatiron)': {
    venueName: 'SPIN New York',
    location: 'Flatiron',
    neighborhood: 'Midtown',
    description: 'Table-tennis-centered social club with bar, events, and group bookings.',
    city: 'NYC'
  },
  'SPIN (NYC - Midtown)': {
    venueName: 'SPIN New York',
    location: 'Midtown East',
    neighborhood: 'Midtown',
    description: 'Table-tennis-centered social club with bar, events, and group bookings.',
    city: 'NYC'
  },
  'T-Squared Social': {
    venueName: 'T-Squared Social',
    location: 'Midtown East',
    neighborhood: 'Midtown',
    description: 'Sports bar centered on multi-sport simulators, games, and large-screen viewing',
    city: 'NYC'
  },
  'Lucky Strike (Times Square)': {
    venueName: 'Lucky Strike Bowling',
    location: 'Times Square',
    neighborhood: 'Midtown',
    description: 'Bowling-based entertainment venue with arcade games and bar space',
    city: 'NYC'
  },
  'Lucky Strike (Chelsea Piers)': {
    venueName: 'Lucky Strike Bowling',
    location: 'Chelsea Piers',
    neighborhood: 'Midtown',
    description: 'F1-themed racing simulators with elevated food and drink',
    city: 'NYC'
  },
  'The Lawn Club (Financial District)': {
    venueName: 'The Lawn Club',
    location: 'Financial District',
    neighborhood: 'Downtown',
    description: 'Indoor lawn games (bocce, cornhole, croquet) and bar',
    city: 'NYC',
    activities: ['Croquet Lawns', 'Curling Lawns', 'Indoor Gaming']
  },
  'Lawn Club (Croquet Lawns)': {
    venueName: 'The Lawn Club',
    location: 'Financial District',
    neighborhood: 'Downtown',
    description: 'Indoor lawn games (bocce, cornhole, croquet) and bar',
    city: 'NYC',
    activities: ['Croquet Lawns', 'Curling Lawns', 'Indoor Gaming']
  },
  'Lawn Club (Curling Lawns)': {
    venueName: 'The Lawn Club',
    location: 'Financial District',
    neighborhood: 'Downtown',
    description: 'Indoor lawn games (bocce, cornhole, croquet) and bar',
    city: 'NYC',
    activities: ['Croquet Lawns', 'Curling Lawns', 'Indoor Gaming']
  },
  'Lawn Club (Indoor Gaming)': {
    venueName: 'The Lawn Club',
    location: 'Financial District',
    neighborhood: 'Downtown',
    description: 'Indoor lawn games (bocce, cornhole, croquet) and bar',
    city: 'NYC',
    activities: ['Croquet Lawns', 'Curling Lawns', 'Indoor Gaming']
  },
  'Kick Axe (Brooklyn)': {
    venueName: 'Kick Axe',
    location: 'Gowanus',
    neighborhood: 'Brooklyn/Queens',
    description: 'Lodge-style axe-throwing bar with events',
    city: 'NYC'
  },
  'Chelsea Piers Golf': {
    venueName: 'Chelsea Piers',
    location: 'Chelsea',
    neighborhood: 'Midtown',
    description: 'Large-scale golf practice facility with river views',
    city: 'NYC'
  }
};

// London venues metadata
const londonVenues = {
  'Topgolf Chigwell': {
    venueName: 'Topgolf',
    location: 'Chigwell',
    neighborhood: null,
    description: 'Large-format, technology-enabled driving range combining golf games with food and beverage',
    city: 'London'
  },
  'Puttshack (Bank)': {
    venueName: 'Puttshack',
    location: 'Bank',
    neighborhood: 'The City',
    description: 'Tech-enabled crazy golf',
    city: 'London'
  },
  'Puttshack (Lakeside)': {
    venueName: 'Puttshack',
    location: 'Westfield',
    neighborhood: null,
    description: 'Tech-enabled crazy golf',
    city: 'London'
  },
  'Puttshack (White City)': {
    venueName: 'Puttshack',
    location: 'White City',
    neighborhood: null,
    description: 'Tech-enabled crazy golf',
    city: 'London'
  },
  'Puttshack (Watford)': {
    venueName: 'Puttshack',
    location: 'Watford',
    neighborhood: null,
    description: 'Tech-enabled crazy golf',
    city: 'London'
  },
  'Swingers (London)': {
    venueName: 'Swingers',
    location: 'Oxford Circus',
    neighborhood: 'West End',
    description: 'Adults-only mini-golf paired with street-food style dining and bar service',
    city: 'London'
  },
  'Flight Club Darts (Shoreditch)': {
    venueName: 'Flight Club',
    location: 'Shoreditch',
    neighborhood: 'The City',
    description: 'Tech-enabled social darts with automated scoring and group games',
    city: 'London'
  },
  'Flight Club Darts (Bloomsbury)': {
    venueName: 'Flight Club',
    location: 'Bloomsbury',
    neighborhood: 'West End',
    description: 'Tech-enabled social darts with automated scoring and group games',
    city: 'London'
  },
  'Flight Club Darts (Victoria)': {
    venueName: 'Flight Club',
    location: 'Victoria',
    neighborhood: 'Westminster',
    description: 'Tech-enabled social darts with automated scoring and group games',
    city: 'London'
  },
  'Flight Club Darts (Angel)': {
    venueName: 'Flight Club',
    location: 'Islington',
    neighborhood: 'The City',
    description: 'Tech-enabled social darts with automated scoring and group games',
    city: 'London'
  },
  'Electric Shuffle (London)': {
    venueName: 'Electric Shuffle',
    location: 'Canary Wharf',
    neighborhood: 'Canary Wharf',
    description: 'Technology-enabled shuffleboard with TV screens and restaurant service',
    city: 'London'
  },
  'Electric Shuffle (London Bridge)': {
    venueName: 'Electric Shuffle',
    location: 'London Bridge',
    neighborhood: 'The City',
    description: 'Technology-enabled shuffleboard with TV screens and restaurant service',
    city: 'London'
  },
  'Electric Shuffle (King\'s Cross)': {
    venueName: 'Electric Shuffle',
    location: 'King\'s Cross',
    neighborhood: null,
    description: 'Technology-enabled shuffleboard with TV screens and restaurant service',
    city: 'London'
  },
  'Clays Bar (Canary Wharf)': {
    venueName: 'Clays',
    location: 'Canary Wharf',
    neighborhood: 'Canary Wharf',
    description: 'Virtual clay shooting using simulated targets in an indoor bar environment',
    city: 'London'
  },
  'Clays Bar (The City)': {
    venueName: 'Clays',
    location: 'Moorgate',
    neighborhood: 'The City',
    description: 'Virtual clay shooting using simulated targets in an indoor bar environment',
    city: 'London'
  },
  'Clays Bar (Soho)': {
    venueName: 'Clays',
    location: 'Soho',
    neighborhood: 'West End',
    description: 'Virtual clay shooting using simulated targets in an indoor bar environment',
    city: 'London'
  },
  'F1 Arcade': {
    venueName: 'F1 Arcade',
    location: 'St Paul\'s',
    neighborhood: 'The City',
    description: 'F1-themed racing simulators with elevated food and drink',
    city: 'London'
  },
  'Fair Game (Canary Wharf)': {
    venueName: 'Fairgame',
    location: 'Canary Wharf',
    neighborhood: 'Canary Wharf',
    description: 'Competitive fairground games in an adult social setting',
    city: 'London'
  },
  'Fair Game (City)': {
    venueName: 'Fairgame',
    location: 'St Paul\'s',
    neighborhood: 'The City',
    description: 'Competitive fairground games in an adult social setting',
    city: 'London'
  },
  'Bounce': {
    venueName: 'Bounce',
    location: 'Farringdon',
    neighborhood: 'The City',
    description: 'Table-tennis-led social venue with food, drink, and group play',
    city: 'London'
  },
  'All Star Lanes (Holborn)': {
    venueName: 'All Star Lanes',
    location: 'Holborn',
    neighborhood: 'West End',
    description: 'Boutique bowling concept combined with karaoke, dining, and bar space',
    city: 'London'
  },
  'All Star Lanes (Shoreditch)': {
    venueName: 'All Star Lanes',
    location: 'Shoreditch',
    neighborhood: 'The City',
    description: 'Boutique bowling concept combined with karaoke, dining, and bar space',
    city: 'London'
  },
  'All Star Lanes (White City)': {
    venueName: 'All Star Lanes',
    location: 'White City',
    neighborhood: null,
    description: 'Boutique bowling concept combined with karaoke, dining, and bar space',
    city: 'London'
  },
  'All Star Lanes (Stratford)': {
    venueName: 'All Star Lanes',
    location: 'Stratford',
    neighborhood: null,
    description: 'Boutique bowling concept combined with karaoke, dining, and bar space',
    city: 'London'
  },
  'Hijingo': {
    venueName: 'Hijingo',
    location: 'Shoreditch',
    neighborhood: 'The City',
    description: 'Technology-driven bingo experience adapted for nightlife and group entertainment',
    city: 'London'
  }
};

// Combined metadata
const venueMetadata = {
  ...nycVenues,
  ...londonVenues
};

// Get metadata for a venue name
export const getVenueMetadata = (venueName) => {
  if (!venueName) return null;
  
  // Direct lookup
  if (venueMetadata[venueName]) {
    return venueMetadata[venueName];
  }
  
  // Try to match by normalizing
  const normalized = normalizeVenueName(venueName);
  for (const [key, value] of Object.entries(venueMetadata)) {
    if (normalizeVenueName(key) === normalized) {
      return value;
    }
  }
  
  // Try to match by base name and location extraction
  const baseName = getBaseVenueName(venueName);
  const location = extractLocation(venueName);
  
  if (baseName && location) {
    for (const [key, value] of Object.entries(venueMetadata)) {
      const keyBase = getBaseVenueName(key);
      const keyLocation = extractLocation(key) || venueMetadata[key]?.location;
      
      if (normalizeVenueName(keyBase) === normalizeVenueName(baseName) &&
          normalizeVenueName(keyLocation) === normalizeVenueName(location)) {
        return value;
      }
    }
  }
  
  return null;
};

// Get all neighborhoods for a city
export const getNeighborhoodsForCity = (city) => {
  const neighborhoods = new Set();
  
  for (const metadata of Object.values(venueMetadata)) {
    if (metadata.city === city && metadata.neighborhood) {
      neighborhoods.add(metadata.neighborhood);
    }
  }
  
  return Array.from(neighborhoods).sort();
};

// Get all venues for a neighborhood
export const getVenuesForNeighborhood = (neighborhood, city) => {
  const venues = [];
  
  for (const [venueName, metadata] of Object.entries(venueMetadata)) {
    if (metadata.neighborhood === neighborhood && metadata.city === city) {
      venues.push(venueName);
    }
  }
  
  return venues;
};

// Get all unique venue base names (for grouping)
export const getAllVenueBaseNames = () => {
  const baseNames = new Set();
  
  for (const metadata of Object.values(venueMetadata)) {
    baseNames.add(metadata.venueName);
  }
  
  return Array.from(baseNames).sort();
};

export default venueMetadata;
