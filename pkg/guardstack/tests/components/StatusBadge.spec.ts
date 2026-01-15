/**
 * StatusBadge Component Tests
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import StatusBadge from '../../components/StatusBadge.vue';

describe('StatusBadge', () => {
  it('renders with status text', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'active' },
    });

    expect(wrapper.text()).toContain('Active');
  });

  it('renders pending status correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'pending' },
    });

    expect(wrapper.text()).toContain('Pending');
    expect(wrapper.classes().join(' ')).toMatch(/yellow|amber/);
  });

  it('renders completed status correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'completed' },
    });

    expect(wrapper.text()).toContain('Completed');
    expect(wrapper.classes().join(' ')).toMatch(/green/);
  });

  it('renders error status correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'error' },
    });

    expect(wrapper.text()).toContain('Error');
    expect(wrapper.classes().join(' ')).toMatch(/red/);
  });

  it('renders running status correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'running' },
    });

    expect(wrapper.text()).toContain('Running');
    expect(wrapper.classes().join(' ')).toMatch(/blue/);
  });

  it('handles unknown status gracefully', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'unknown-status' },
    });

    expect(wrapper.text()).toContain('Unknown Status');
  });

  it('applies small size class', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'active', size: 'sm' },
    });

    expect(wrapper.classes().join(' ')).toMatch(/text-xs|px-2|py-0.5/);
  });

  it('applies large size class', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'active', size: 'lg' },
    });

    expect(wrapper.classes().join(' ')).toMatch(/text-base|px-4|py-1.5/);
  });
});
