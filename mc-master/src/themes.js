// Theme definitions
export const themes = {
  ruby: {
    name: 'Ruby',
    primary: '#DC2626',
    primaryDark: '#991B1B',
    primaryLight: '#EF4444',
    secondary: '#DC2626',
    tertiary: '#DC2626',
    accent: '#F87171',
    offWhite: '#FAF9F6',
    offWhiteDark: '#F5F5F0',
    text: '#1F1F1F',
    textLight: '#4A4A4A',
    // For avatar parts
    eyeColor: '#DC2626',
    mouthColor: '#DC2626',
    ringColor1: '#DC2626',
    ringColor2: '#EF4444',
  },
  spectrum: {
    name: 'Spectrum',
    primary: '#2563EB', // Blue
    primaryDark: '#1D4ED8',
    primaryLight: '#3B82F6',
    secondary: '#DC2626', // Red
    tertiary: '#16A34A', // Green
    accent: '#60A5FA',
    offWhite: '#FAF9F6',
    offWhiteDark: '#F5F5F0',
    text: '#1F1F1F',
    textLight: '#4A4A4A',
    // For avatar parts - multicolor
    eyeColor: '#2563EB', // Blue eyes
    mouthColor: '#DC2626', // Red mouth
    ringColor1: '#16A34A', // Green ring
    ringColor2: '#2563EB', // Blue ring
  },
}

export const getThemeColors = (themeName) => {
  return themes[themeName] || themes.ruby
}
