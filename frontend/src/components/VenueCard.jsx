import { formatVenueName, isLawnClubVenue, getLawnClubActivities } from '../utils/venueFormatting'
import { getVenueMetadata } from '../data/venueMetadata'

// Map venue names to image filenames in the public folder
const VENUE_IMAGE_MAP = {
  'Swingers (Nomad)': 'Swingers.webp',
  'Swingers (Oxford Circus)': 'Swingers.webp',
  'Electric Shuffle (Nomad)': 'Electric Shuffle.webp',
  'Electric Shuffle (Canary Wharf)': 'Electric Shuffle.webp',
  'Electric Shuffle (London Bridge)': 'Electric Shuffle.webp',
  'Electric Shuffle (King\'s Cross)': 'Electric Shuffle.webp',
  'Lawn Club (Indoor Gaming)': 'LawnClub.webp',
  'Lawn Club (Curling Lawns)': 'LawnClubCurlingNewYork.jpg',
  'Lawn Club (Croquet Lawns)': 'LawnClubCroquetNewYork.webp',
  'The Lawn Club (Financial District)': 'LawnClub.webp',
  'SPIN (Midtown East)': 'spin_midtown.webp', 
  'SPIN (Flatiron)': 'spin_flatrion.webp', 
  'Five Iron Golf (Financial District)': 'FiveIron.webp',
  'Five Iron Golf (Flatiron)': 'FiveIron.webp',
  'Five Iron Golf (Midtown East)': 'FiveIron.webp',
  'Five Iron Golf (Herald Square)': 'FiveIron.webp',
  'Five Iron Golf (Long Island City)': 'FiveIron.webp',
  'Five Iron Golf (Upper East Side)': 'FiveIron.webp',
  'Five Iron Golf (Rockefeller Center)': 'FiveIron.webp',
  'Lucky Strike (Chelsea Piers)': 'LuckyStrike.webp', 
  'Lucky Strike (Times Square)': 'LuckyStrike.webp', 
  'Frames Bowling Lounge (Midtown)': 'Frames.webp', 
  'Fair Game (Canary Wharf)': 'Fairgame.webp',
  'Fair Game (City)': 'Fairgame.webp',
  'Clays Bar (Canary Wharf)': 'Clays.webp', 
  'Clays Bar (The City)': 'Clays.webp', 
  'Clays Bar (Birmingham)': 'Clays.webp', 
  'Clays Bar (Soho)': 'Clays.webp', 
  'Puttshack (Bank)': 'Puttshack.webp',
  'Puttshack (Lakeside)': 'Puttshack.webp',
  'Puttshack (White City)': 'Puttshack.webp',
  'Puttshack (Watford)': 'Puttshack.webp',
  'Flight Club Darts (Angel)': 'Flight Club.webp',
  'Flight Club Darts (Bloomsbury)': 'Flight Club.webp',
  'Flight Club Darts (Shoreditch)': 'Flight Club.webp',
  'Flight Club Darts (Victoria)': 'Flight Club.webp',
  'F1 Arcade (St Paul\'s)': 'F1 Arcade.webp',
  'Chelsea Piers (Chelsea)': 'daysmart.webp',
  'Topgolf (Chigwell)': 'topgolfchigwell.webp',
  'T-Squared Social (Midtown East)': 'tsquaredsocial.webp',
  'Hijingo (Shoreditch)': 'hijingo.webp',
  'Bounce (Farringdon)': 'Bounce.webp',
  'Bounce (Shoreditch)': 'Bounce.webp',
  'Puttery (Meatpacking)': 'Puttery.webp',
  'Kick Axe (Brooklyn)': 'kickaxe.webp',
  'All Star Lanes (Stratford)': 'AllStarLanes.webp',
  'All Star Lanes (Holborn)': 'AllStarLanes.webp',
  'All Star Lanes (White City)': 'AllStarLanes.webp',
  'All Star Lanes (Brick Lane)': 'AllStarLanes.webp',
  'All Star Lanes (Shoreditch)': 'AllStarLanes.webp',
}

function VenueCard({ venueName, slotCount, onClick, city = null }) {
  const getVenueImage = (venueName) => {
    const imageFile = VENUE_IMAGE_MAP[venueName] || 'sample.webp'
    return `/${imageFile}`
  }

  const formatSlotCount = (count) => {
    if (count === 0) return 'No slots available'
    if (count === 1) return '1 available slot'
    return `${count} available slots`
  }

  // Format venue name and get metadata
  const formattedName = formatVenueName(venueName, city)
  const metadata = getVenueMetadata(venueName)
  const description = metadata?.description || ''
  const isLawnClub = isLawnClubVenue(venueName)
  const activities = isLawnClub ? getLawnClubActivities(venueName) : []

  return (
    <div 
      className="venue-card" 
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
    >
      <div className="venue-card-image-container">
        <img 
          src={getVenueImage(venueName)} 
          alt={formattedName}
          className="venue-card-image"
          onError={(e) => {
            e.target.src = '/sample.webp'
          }}
        />
      </div>
      <div className="venue-card-content">
        <div className="venue-card-name">{formattedName}</div>
        {isLawnClub && activities.length > 0 && (
          <div className="venue-card-activities">
            {activities.join(', ')}
          </div>
        )}
        {description && (
          <div className="venue-card-description">{description}</div>
        )}
        <div className="venue-card-slots">{formatSlotCount(slotCount)}</div>
      </div>
    </div>
  )
}

export default VenueCard
