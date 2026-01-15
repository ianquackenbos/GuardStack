/**
 * ScoreGauge Component Tests
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ScoreGauge from '../../components/ScoreGauge.vue';

describe('ScoreGauge', () => {
  it('renders with default props', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 75 },
    });

    expect(wrapper.find('svg').exists()).toBe(true);
    expect(wrapper.text()).toContain('75');
    expect(wrapper.text()).toContain('/ 100');
  });

  it('normalizes score to 0-100 range', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 150 },
    });

    expect(wrapper.text()).toContain('100');
  });

  it('handles negative scores', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: -10 },
    });

    expect(wrapper.text()).toContain('0');
  });

  it('renders small size correctly', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 50, size: 'sm' },
    });

    const svg = wrapper.find('svg');
    expect(svg.attributes('width')).toBe('80');
    expect(svg.attributes('height')).toBe('80');
  });

  it('renders large size correctly', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 50, size: 'lg' },
    });

    const svg = wrapper.find('svg');
    expect(svg.attributes('width')).toBe('160');
    expect(svg.attributes('height')).toBe('160');
  });

  it('shows label when showLabel is true', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 85, showLabel: true },
    });

    expect(wrapper.text()).toContain('Minimal Risk');
  });

  it('shows custom label', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 50, showLabel: true, label: 'Custom Label' },
    });

    expect(wrapper.text()).toContain('Custom Label');
  });

  it('applies correct color for critical risk (0-29)', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 15 },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.attributes('stroke')).toBe('#ef4444');
  });

  it('applies correct color for high risk (30-49)', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 35 },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.attributes('stroke')).toBe('#f97316');
  });

  it('applies correct color for medium risk (40-59)', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 45 },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.attributes('stroke')).toBe('#eab308');
  });

  it('applies correct color for low risk (60-79)', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 70 },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.attributes('stroke')).toBe('#22c55e');
  });

  it('applies correct color for minimal risk (80+)', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 90 },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.attributes('stroke')).toBe('#10b981');
  });

  it('has animation class when animated prop is true', () => {
    const wrapper = mount(ScoreGauge, {
      props: { score: 75, animated: true },
    });

    const circles = wrapper.findAll('circle');
    const scoreCircle = circles[1];
    expect(scoreCircle.classes()).toContain('transition-all');
    expect(scoreCircle.classes()).toContain('duration-1000');
  });
});
