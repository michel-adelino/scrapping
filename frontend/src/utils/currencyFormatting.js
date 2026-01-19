// Utility functions for formatting currency

/**
 * Formats a price string to always show 2 decimal places
 * @param {string|number} price - Price as string or number (e.g., "$37.5", "$37", "37.5", 37.5)
 * @returns {string} - Formatted price with 2 decimal places (e.g., "$37.50")
 */
export const formatPrice = (price) => {
  if (!price || price === '-' || price === '') return '-';
  
  // Convert to string if number
  let priceStr = String(price).trim();
  
  // Remove currency symbols and whitespace
  priceStr = priceStr.replace(/[$£€,]/g, '').trim();
  
  // Try to extract numeric value
  const numericMatch = priceStr.match(/(\d+\.?\d*)/);
  if (!numericMatch) {
    // If no numeric value found, return as-is
    return String(price);
  }
  
  const numericValue = parseFloat(numericMatch[1]);
  
  // Check if it's NaN
  if (isNaN(numericValue)) {
    return String(price);
  }
  
  // Format to 2 decimal places
  const formatted = numericValue.toFixed(2);
  
  // Determine currency symbol (default to $)
  let currencySymbol = '$';
  const originalPrice = String(price);
  if (originalPrice.includes('£')) {
    currencySymbol = '£';
  } else if (originalPrice.includes('€')) {
    currencySymbol = '€';
  } else if (originalPrice.includes('$')) {
    currencySymbol = '$';
  }
  
  return `${currencySymbol}${formatted}`;
};

/**
 * Formats a price range
 * @param {string} priceRange - Price range string (e.g., "$37.5 - $50")
 * @returns {string} - Formatted price range
 */
export const formatPriceRange = (priceRange) => {
  if (!priceRange || priceRange === '-') return '-';
  
  // Split by common separators
  const parts = priceRange.split(/[-–—]/).map(p => p.trim());
  
  if (parts.length === 1) {
    return formatPrice(parts[0]);
  }
  
  return parts.map(p => formatPrice(p)).join(' - ');
};
