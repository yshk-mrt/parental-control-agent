import React from 'react';

// 一時的なcn関数
const cn = (...classes: (string | undefined)[]) => classes.filter(Boolean).join(' ');

interface LayoutProps {
  children: React.ReactNode;
  className?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, className }) => {
  return (
    <div className={cn('min-h-screen bg-gray-50 text-gray-900', className)}>
      {children}
    </div>
  );
};

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
}

const Container: React.FC<ContainerProps> = ({ 
  children, 
  className, 
  maxWidth = 'xl' 
}) => {
  const maxWidths = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-4xl',
    '2xl': 'max-w-6xl',
    full: 'max-w-full',
  };

  return (
    <div className={cn(
      'mx-auto px-4 sm:px-6 lg:px-8',
      maxWidths[maxWidth],
      className
    )}>
      {children}
    </div>
  );
};

interface PageHeaderProps {
  title: string;
  description?: string;
  className?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, description, className }) => {
  return (
    <div className={cn('mb-8', className)}>
      <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
      {description && (
        <p className="mt-2 text-muted-foreground">{description}</p>
      )}
    </div>
  );
};

export { Layout, Container, PageHeader }; 