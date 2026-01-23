// Utility functions for formatting venue names

/**
 * Formats venue name from "Venue Name (City - Location)" to "Venue Name (Location)"
 * @param {string} venueName - The venue name as stored in database
 * @param {string} city - Optional city to help with formatting
 * @returns {string} - Formatted venue name
 */
export const formatVenueName = (venueName, city = null) => {
  if (!venueName) return '';
  
  // Remove city prefix from patterns like "(NYC - Location)" or "(London - Location)"
  let formatted = venueName.replace(/\s*\(NYC\s*-\s*/gi, ' (');
  formatted = formatted.replace(/\s*\(London\s*-\s*/gi, ' (');
  
  // If still has city prefix, try to remove it
  if (city) {
    const cityPattern = new RegExp(`\\s*\\(${city}\\s*-\s*`, 'gi');
    formatted = formatted.replace(cityPattern, ' (');
  }
  
  return formatted;
};

/**
 * Extracts the base venue name without location
 * @param {string} venueName - The venue name
 * @returns {string} - Base venue name
 */
export const getBaseVenueName = (venueName) => {
  if (!venueName) return '';
  
  // Remove location in parentheses
  return venueName.replace(/\s*\([^)]*\)\s*$/, '').trim();
};

/**
 * Extracts the location from venue name
 * @param {string} venueName - The venue name
 * @returns {string|null} - Location or null
 */
export const getLocationFromVenueName = (venueName) => {
  if (!venueName) return null;
  
  const match = venueName.match(/\(([^)]+)\)/);
  if (match) {
    const locationPart = match[1];
    // Remove city prefix
    return locationPart.replace(/^(NYC|London)\s*-\s*/i, '').trim();
  }
  
  return null;
};

/**
 * Checks if venue is a Lawn Club venue with activities
 * @param {string} venueName - The venue name
 * @returns {boolean} - True if Lawn Club venue
 */
export const isLawnClubVenue = (venueName) => {
  if (!venueName) return false;
  return venueName.toLowerCase().includes('lawn club');
};

/**
 * Gets activities for Lawn Club venue
 * @param {string} venueName - The venue name
 * @returns {string[]} - Array of activity names
 */
export const getLawnClubActivities = (venueName) => {
  if (!isLawnClubVenue(venueName)) return [];
  
  const activities = ['Croquet Lawns', 'Curling Lawns', 'Indoor Gaming'];
  
  // Check if current venue name indicates a specific activity
  const activityMatch = venueName.match(/\(([^)]+)\)/);
  if (activityMatch) {
    const activity = activityMatch[1];
    // If it's one of the activities, return all activities
    if (activities.some(a => activity.includes(a.split(' ')[0]))) {
      return activities;
    }
  }
  
  return activities;
};
