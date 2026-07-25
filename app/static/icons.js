// Ícones em silhueta simples por tipo de equipamento, usados no painel.
// Todos em viewBox 0 0 48 32, usando currentColor (herda a cor do texto do card).

const EQUIPMENT_ICONS = {
  truck: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 22 L2 12 L20 8 L20 22 Z" fill="currentColor" opacity=".85"/>
      <path d="M20 10 L34 10 L40 16 L40 22 L20 22 Z" fill="currentColor"/>
      <rect x="30" y="12" width="6" height="6" fill="#0d0d0d" opacity=".4"/>
      <circle cx="11" cy="24" r="4.2" fill="currentColor"/>
      <circle cx="11" cy="24" r="1.6" fill="#0d0d0d"/>
      <circle cx="34" cy="24" r="4.2" fill="currentColor"/>
      <circle cx="34" cy="24" r="1.6" fill="#0d0d0d"/>
    </svg>`,

  excavator: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="22" width="30" height="4" rx="1" fill="currentColor" opacity=".55"/>
      <rect x="10" y="14" width="18" height="9" rx="2" fill="currentColor"/>
      <path d="M24 15 L36 8 L34 6 L40 4 L42 9 L34 15 Z" fill="currentColor"/>
      <circle cx="12" cy="26" r="2.6" fill="currentColor" opacity=".7"/>
      <circle cx="20" cy="26" r="2.6" fill="currentColor" opacity=".7"/>
      <circle cx="30" cy="26" r="2.6" fill="currentColor" opacity=".7"/>
    </svg>`,

  loader: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="16" y="10" width="20" height="10" rx="2" fill="currentColor"/>
      <path d="M4 24 L4 18 L12 14 L16 14 L16 22 L10 24 Z" fill="currentColor" opacity=".85"/>
      <path d="M2 26 L10 26 L10 20 L4 22 Z" fill="currentColor"/>
      <circle cx="14" cy="26" r="4" fill="currentColor"/>
      <circle cx="14" cy="26" r="1.5" fill="#0d0d0d"/>
      <circle cx="32" cy="26" r="4" fill="currentColor"/>
      <circle cx="32" cy="26" r="1.5" fill="#0d0d0d"/>
    </svg>`,

  dozer: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="14" y="10" width="22" height="9" rx="2" fill="currentColor"/>
      <rect x="4" y="16" width="8" height="10" fill="currentColor" opacity=".9"/>
      <rect x="6" y="22" width="34" height="5" rx="2.5" fill="currentColor" opacity=".55"/>
      <rect x="6" y="22" width="34" height="5" rx="2.5" fill="none" stroke="currentColor" stroke-dasharray="2 2"/>
    </svg>`,

  wheel_dozer: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="14" y="10" width="22" height="9" rx="2" fill="currentColor"/>
      <rect x="4" y="16" width="8" height="10" fill="currentColor" opacity=".9"/>
      <circle cx="16" cy="27" r="4" fill="currentColor"/>
      <circle cx="34" cy="27" r="4" fill="currentColor"/>
    </svg>`,

  drill: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="2" width="4" height="24" fill="currentColor"/>
      <rect x="8" y="22" width="32" height="6" rx="2" fill="currentColor" opacity=".85"/>
      <circle cx="14" cy="28" r="2.4" fill="currentColor"/>
      <circle cx="34" cy="28" r="2.4" fill="currentColor"/>
    </svg>`,

  grader: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="18" y="10" width="18" height="8" rx="2" fill="currentColor"/>
      <path d="M2 20 L46 20" stroke="currentColor" stroke-width="2"/>
      <path d="M6 27 L14 20 L20 20 L18 27 Z" fill="currentColor" opacity=".8"/>
      <circle cx="12" cy="27" r="2.6" fill="currentColor"/>
      <circle cx="40" cy="27" r="2.6" fill="currentColor"/>
    </svg>`,

  shovel: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="8" y="16" width="24" height="10" rx="2" fill="currentColor"/>
      <path d="M22 16 L38 6 L44 10 L30 20 Z" fill="currentColor"/>
      <path d="M38 6 L44 4 L46 10 L44 10 Z" fill="currentColor" opacity=".8"/>
      <rect x="8" y="26" width="24" height="3" fill="currentColor" opacity=".5"/>
    </svg>`,

  support: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 24 L6 16 L16 16 L20 12 L34 12 L34 24 Z" fill="currentColor"/>
      <rect x="20" y="14" width="12" height="8" fill="#0d0d0d" opacity=".35"/>
      <circle cx="13" cy="26" r="3.4" fill="currentColor"/>
      <circle cx="29" cy="26" r="3.4" fill="currentColor"/>
    </svg>`,

  light_vehicle: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M8 22 L10 15 L18 12 L30 12 L34 17 L40 18 L40 22 Z" fill="currentColor"/>
      <rect x="19" y="13" width="9" height="6" fill="#0d0d0d" opacity=".35"/>
      <circle cx="15" cy="24" r="3.2" fill="currentColor"/>
      <circle cx="33" cy="24" r="3.2" fill="currentColor"/>
    </svg>`,

  generic: `
    <svg viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="12" y="8" width="24" height="16" rx="3" fill="currentColor" opacity=".7"/>
      <text x="24" y="21" font-size="14" text-anchor="middle" fill="#0d0d0d" font-family="monospace">?</text>
    </svg>`,
};

function getEquipmentIcon(key){
  return EQUIPMENT_ICONS[key] || EQUIPMENT_ICONS.generic;
}
