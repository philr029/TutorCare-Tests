import { TestSectionCard } from '../components/dashboard/TestSectionCard';
import { testSections } from '../data/mockTests';
import { EmptyState } from '../components/ui/EmptyState';
import type { TestCategory } from '../types';

interface CategoryPageProps {
  category: TestCategory;
}

export function CategoryPage({ category }: CategoryPageProps) {
  const sections = testSections.filter(s => s.category === category);

  if (sections.length === 0) {
    return (
      <EmptyState
        title="No tests found"
        description="There are no tests defined for this category yet."
        icon="📭"
      />
    );
  }

  return (
    <div className="space-y-4 max-w-4xl">
      {sections.map(section => (
        <TestSectionCard key={section.id} section={section} />
      ))}
    </div>
  );
}
