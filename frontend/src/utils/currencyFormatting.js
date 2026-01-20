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
  
  // Check if the string matches or contains a non-price term
  if (nonPriceTerms.some(term => lowerPrice === term || lowerPrice.includes(term))) {
    return null;
  }
  
  // Check if it's a description containing words (not just numbers/currency)
  // If it has multiple words and no currency, it's likely descriptive
  const wordCount = lowerPrice.split(/\s+/).filter(word => word.length > 0).length;
  const hasCurrency = /[$£€]/.test(originalPrice);
  
  // If it has multiple words but no currency, it's likely descriptive text
  if (wordCount > 3 && !hasCurrency) {
    return null;
  }
  
  // If has currency symbol, it's likely a real price - extract and format
  if (hasCurrency) {
    // Remove currency symbols and commas for parsing
    let priceStr = originalPrice.replace(/[$£€,]/g, '').trim();
    
    // Try to extract first numeric value
    const numericMatch = priceStr.match(/(\d+\.?\d*)/);
    if (!numericMatch) {
      // Has currency but no number - not a valid price
      return null;
    }
    
    const numericValue = parseFloat(numericMatch[1]);
    if (isNaN(numericValue)) {
      // Can't parse number - not a valid price
      return null;
    }
    
    // Format to 2 decimal places
    const formatted = numericValue.toFixed(2);
    
    // Determine currency symbol from original
    let currencySymbol = '$';
    if (originalPrice.includes('£')) {
      currencySymbol = '£';
    } else if (originalPrice.includes('€')) {
      currencySymbol = '€';
    }
    
    // If original had complex format (like "1h : $45"), preserve it
    // Only reformat if it's a simple price format
    const simpleFormat = /^[$£€]?\s*\d+\.?\d*\s*[$£€]?$/;
    if (simpleFormat.test(originalPrice)) {
      return `${currencySymbol}${formatted}`;
    }
    
    // For complex formats with currency, return as-is (e.g., "1h : $45")
    return originalPrice;
  }
  
  // No currency symbol - check if it's a pure numeric value
  const pureNumeric = /^\d+\.?\d*$/;
  if (pureNumeric.test(lowerPrice)) {
    const numericValue = parseFloat(lowerPrice);
    if (!isNaN(numericValue)) {
      return `$${numericValue.toFixed(2)}`;
    }
  }
  
  // Otherwise, it's descriptive text - return null to hide
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
