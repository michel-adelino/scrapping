// Utility functions for formatting currency

/**
 * Formats a price string to always show 2 decimal places
 * Returns null if price is not a real monetary value
 * @param {string|number} price - Price as string or number (e.g., "$37.5", "$37", "37.5", 37.5)
 * @returns {string|null} - Formatted price with 2 decimal places (e.g., "$37.50") or null if not a price
 */
export const formatPrice = (price) => {
  if (!price || price === '-' || price === '') return null;
  
  // Convert to string if number
  const originalPrice = String(price).trim();
  const lowerPrice = originalPrice.toLowerCase();
  
  // Expanded blacklist of common non-price descriptive text
  const nonPriceTerms = [
    'available',
    'none',
    'closed',
    'full',
    'sold out',
    'n/a',
    'unavailable',
    'sold',
    'booking required',
    'call for pricing',
    'varies',
    'last few',
    'low stock',
    'few left',
    'limited',
    'reservation',
    'book now',
    'enquire',
    'contact',
    'tbd',
    'pending',
    'waitlist',
    'quote'
  ];
  
  // Check if the entire string matches a non-price term (without numbers)
  if (nonPriceTerms.some(term => lowerPrice === term)) {
    return null;
  }
  
  // Check if it contains a non-price term AND no numbers
  const hasNumbers = /\d/.test(originalPrice);
  if (!hasNumbers && nonPriceTerms.some(term => lowerPrice.includes(term))) {
    return null;
  }
  
  // Check if it's a description containing words (not just numbers/currency)
  // If it has multiple words and no currency/numbers, it's likely descriptive text
  const wordCount = lowerPrice.split(/\s+/).filter(word => word.length > 0).length;
  const hasCurrency = /[$£€]/.test(originalPrice);
  
  // If it has many words but no currency and no numbers, it's likely descriptive text
  if (wordCount > 3 && !hasCurrency && !hasNumbers) {
    return null;
  }
  
  // Try to extract currency symbol and numeric value
  // Match patterns like: $45, £30.50, €20, 45.00, $45.00, "1h : $45", etc.
  let currencySymbol = '$'; // Default currency
  let numericValue = null;
  
  // First, check if there's a currency symbol and extract it
  if (originalPrice.includes('£')) {
    currencySymbol = '£';
  } else if (originalPrice.includes('€')) {
    currencySymbol = '€';
  } else if (originalPrice.includes('$')) {
    currencySymbol = '$';
  }
  
  // Extract the numeric value (with optional decimal)
  // Look for patterns like: 45, 45.00, 45.5
  const numericMatch = originalPrice.match(/(\d+\.?\d*)/);
  
  if (numericMatch) {
    numericValue = parseFloat(numericMatch[1]);
    
    // Validate the numeric value
    if (!isNaN(numericValue) && numericValue > 0) {
      // Format to exactly 2 decimal places
      return `${currencySymbol}${numericValue.toFixed(2)}`;
    }
  }
  
  // If no valid price found, return null to hide
  return null;
};

/**
 * Formats a price range
 * @param {string} priceRange - Price range string (e.g., "$37.5 - $50")
 * @returns {string|null} - Formatted price range or null if not valid prices
 */
export const formatPriceRange = (priceRange) => {
  if (!priceRange || priceRange === '-') return null;
  
  // Split by common separators
  const parts = priceRange.split(/[-–—]/).map(p => p.trim());
  
  if (parts.length === 1) {
    return formatPrice(parts[0]);
  }
  
  // Format each part and filter out nulls
  const formattedParts = parts.map(p => formatPrice(p)).filter(p => p !== null);
  
  // If no valid prices, return null
  if (formattedParts.length === 0) {
    return null;
  }
  
  return formattedParts.join(' - ');
};
