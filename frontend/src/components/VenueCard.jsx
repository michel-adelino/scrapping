// Map venue names to image filenames in the public folder
const VENUE_IMAGE_MAP = {
  'Swingers (NYC)': 'Swingers.webp',
  'Swingers (London)': 'Swingers.webp',
  'Electric Shuffle (NYC)': 'Electric Shuffle.webp',
  'Electric Shuffle (London)': 'Electric Shuffle.webp',
  'Lawn Club (Indoor Gaming)': 'LawnClub.webp',
  'Lawn Club (Curling Lawns)': 'LawnClubCurlingNewYork.jpg',
  'Lawn Club (Croquet Lawns)': 'LawnClubCroquetNewYork.webp',
  'SPIN (NYC - Midtown)': 'spin_midtown.webp', 
  'SPIN (NYC - Flatiron)': 'spin_flatrion.webp', 
  'Five Iron Golf (NYC - FiDi)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Flatiron)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Grand Central)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Herald Square)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Long Island City)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Upper East Side)': 'FiveIron.webp',
  'Five Iron Golf (NYC - Rockefeller Center)': 'FiveIron.webp',
  'Lucky Strike (Chelsea Piers)': 'LuckyStrike.webp', 
  'Lucky Strike (Times Square)': 'LuckyStrike.webp', 
  'Easybowl (NYC)': 'Frames.webp', 
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
  'F1 Arcade': 'F1 Arcade.webp',
  'Chelsea Piers Golf': 'daysmart.webp',
  'Topgolf Chigwell': 'topgolfchigwell.webp',
  'T-Squared Social': 'tsquaredsocial.webp',
  'Hijingo': 'hijingo.webp',
  'Bounce': 'Bounce.webp',
  'Puttery (NYC)': 'Puttery.webp',
  'Kick Axe (Brooklyn)': 'kickaxe.webp',
  'All Star Lanes (Stratford)': 'AllStarLanes.webp',
  'All Star Lanes (Holborn)': 'AllStarLanes.webp',
  'All Star Lanes (White City)': 'AllStarLanes.webp',
  'All Star Lanes (Brick Lane)': 'AllStarLanes.webp',
}

function VenueCard({ venueName, slotCount, onClick }) {
  const getVenueImage = (venueName) => {
    const imageFile = VENUE_IMAGE_MAP[venueName] || 'sample.webp'
    return `/${imageFile}`
  }

  const formatSlotCount = (count) => {
    if (count === 0) return 'No slots available'
    if (count === 1) return '1 available slot'
    return `${count} available slots`
  }

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
          alt={venueName}
          className="venue-card-image"
          onError={(e) => {
            e.target.src = '/sample.webp'
          }}
        />
      </div>
      <div className="venue-card-content">
        <div className="venue-card-name">{venueName}</div>
        <div className="venue-card-slots">{formatSlotCount(slotCount)}</div>
      </div>
    </div>
  )
}

export default VenueCard
