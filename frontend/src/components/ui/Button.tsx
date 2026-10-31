/**
 * Reusable Button component
 */
import React from 'react'
import { cn } from '@/utils/cn'

type ButtonVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost'
type ButtonSize = 'default' | 'sm' | 'lg' | 'icon'

const variantStyles: Record<ButtonVariant, string> = {
  default: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-600',
  secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus-visible:ring-gray-400',
  destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-600',
  outline: 'border border-gray-300 bg-white hover:bg-gray-50 focus-visible:ring-gray-400',
  ghost: 'hover:bg-gray-100 focus-visible:ring-gray-400',
}

const sizeStyles: Record<ButtonSize, string> = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3',
  lg: 'h-11 rounded-md px-8',
  icon: 'h-10 w-10',
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', isLoading, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
    const variantStyle = variantStyles[variant]
    const sizeStyle = sizeStyles[size]
    
    return (
      <button
        className={cn(baseStyles, variantStyle, sizeStyle, className)}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <span className="inline-block mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent"></span>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'
