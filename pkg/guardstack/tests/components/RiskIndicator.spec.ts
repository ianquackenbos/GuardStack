/**
 * RiskIndicator Component Tests
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RiskIndicator from '../../components/RiskIndicator.vue';

describe('RiskIndicator', () => {
  it('renders critical risk correctly', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'critical' },
    });

    expect(wrapper.text()).toContain('Critical');
    expect(wrapper.classes().join(' ')).toMatch(/red/);
  });

  it('renders high risk correctly', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'high' },
    });

    expect(wrapper.text()).toContain('High');
    expect(wrapper.classes().join(' ')).toMatch(/orange|red/);
  });

  it('renders medium risk correctly', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'medium' },
    });

    expect(wrapper.text()).toContain('Medium');
    expect(wrapper.classes().join(' ')).toMatch(/yellow|amber/);
  });

  it('renders low risk correctly', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'low' },
    });

    expect(wrapper.text()).toContain('Low');
    expect(wrapper.classes().join(' ')).toMatch(/green|blue/);
  });

  it('renders minimal risk correctly', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'minimal' },
    });

    expect(wrapper.text()).toContain('Minimal');
    expect(wrapper.classes().join(' ')).toMatch(/green/);
  });

  it('shows icon when showIcon is true', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'high', showIcon: true },
    });

    // Check for icon element (could be svg, i, or span with icon class)
    const hasIcon = wrapper.find('svg').exists() || 
                    wrapper.find('[class*="icon"]').exists() ||
                    wrapper.find('i').exists();
    expect(hasIcon).toBe(true);
  });

  it('hides icon when showIcon is false', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'high', showIcon: false },
    });

    const iconElement = wrapper.find('svg');
    // Either no icon or hidden
    expect(iconElement.exists()).toBe(false);
  });

  it('applies compact class when compact is true', () => {
    const wrapper = mount(RiskIndicator, {
      props: { level: 'medium', compact: true },
    });

    // Compact should have smaller padding/text
    expect(wrapper.classes().join(' ')).toMatch(/px-1|py-0|text-xs/);
  });
});
