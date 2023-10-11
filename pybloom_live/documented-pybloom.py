"""
This module implements a bloom filter probabilistic data structure and
a Scalable Bloom Filter that grows in size as you add more items to it
without increasing the false positive error_rate.
"""

from __future__ import absolute_import

import copy
import hashlib
import math
from struct import calcsize, pack, unpack

import xxhash

from pybloom_live.utils import is_string_io, range_fn, running_python_3

try:
    import bitarray
except ImportError:
    raise ImportError('pybloom_live requires bitarray >= 0.3.4')


def make_hashfuncs(num_slices, num_bits):
    """
    Generate hash functions for the Bloom filter.

    Args:
        num_slices (int): Number of hash slices.
        num_bits (int): Number of bits.

    Returns:
        callable: A function that generates hash values for a given key.
        hashfn: The hash function used.

    """
    # Choosing format code and chunk size based on the number of bits.
    if num_bits >= (1 << 31):
        fmt_code, chunk_size = 'Q', 8
    elif num_bits >= (1 << 15):
        fmt_code, chunk_size = 'I', 4
    else:
        fmt_code, chunk_size = 'H', 2

    total_hash_bits = 8 * num_slices * chunk_size

    # Choosing the appropriate hash function based on the total number of bits.
    if total_hash_bits > 384:
        hashfn = hashlib.sha512
    elif total_hash_bits > 256:
        hashfn = hashlib.sha384
    elif total_hash_bits > 160:
        hashfn = hashlib.sha256
    elif total_hash_bits > 128:
        hashfn = hashlib.sha1
    else:
        hashfn = xxhash.xxh128

    fmt = fmt_code * (hashfn().digest_size // chunk_size)
    num_salts, extra = divmod(num_slices, len(fmt))

    if extra:
        num_salts += 1

    # Generating salts based on the hash function.
    salts = tuple(hashfn(hashfn(pack('I', i)).digest()) for i in range_fn(0, num_salts))

    def _hash_maker(key):
        """
        Generate a hash for a given key.

        Args:
            key (str): The input key.

        Yields:
            int: Hash values.

        """
        if running_python_3:
            if isinstance(key, str):
                key = key.encode('utf-8')
            else:
                key = str(key).encode('utf-8')
        else:
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            else:
                key = str(key)

        i = 0
        for salt in salts:
            h = salt.copy()
            h.update(key)
            for uint in unpack(fmt, h.digest()):
                yield uint % num_bits
                i += 1
                if i >= num_slices:
                    return

    return _hash_maker, hashfn


class BloomFilter(object):
    """
    Implements a space-efficient probabilistic data structure.

    Args:
        capacity (int): The number of elements the BloomFilter can store.
        error_rate (float): The acceptable false positive error rate.

    Attributes:
        FILE_FMT (bytes): Format for writing to a file.
        error_rate (float): The false positive error rate.
        num_slices (int): Number of hash slices.
        bits_per_slice (int): Number of bits per slice.
        capacity (int): The capacity of the filter.
        num_bits (int): Total number of bits.
        count (int): Number of elements stored in the filter.
        make_hashes (callable): Hash function generator.
        hashfn: The hash function used.

    """

    FILE_FMT = b'<dQQQQ'

    def __init__(self, capacity, error_rate=0.001):
        """
        Initialize the BloomFilter.

        Args:
            capacity (int): The number of elements the BloomFilter can store.
            error_rate (float, optional): The acceptable false positive error rate.

        Raises:
            ValueError: If capacity or error_rate is invalid.

        """
        if not (0 < error_rate < 1):
            raise ValueError("Error_Rate must be between 0 and 1.")
        if not capacity > 0:
            raise ValueError("Capacity must be > 0")

        # Calculate the number of slices and bits per slice.
        num_slices = int(math.ceil(math.log(1.0 / error_rate, 2)))
        bits_per_slice = int(math.ceil(
            (capacity * abs(math.log(error_rate))) /
            (num_slices * (math.log(2) ** 2))))

        self._setup(error_rate, num_slices, bits_per_slice, capacity, 0)
        self.bitarray = bitarray.bitarray(self.num_bits, endian='little')
        self.bitarray.setall(False)

    def _setup(self, error_rate, num_slices, bits_per_slice, capacity, count):
        """
        Set up the BloomFilter attributes.

        Args:
            error_rate (float): The false positive error rate.
            num_slices (int): Number of hash slices.
            bits_per_slice (int): Number of bits per slice.
            capacity (int): The capacity of the filter.
            count (int): Number of elements stored in the filter.

        """
        self.error_rate = error_rate
        self.num_slices = num_slices
        self.bits_per_slice = bits_per_slice
        self.capacity = capacity
        self.num_bits = num_slices * bits_per_slice
        self.count = count
        self.make_hashes, self.hashfn = make_hashfuncs(self.num_slices, self.bits_per_slice)

    def __contains__(self, key):
        """
        Test if a key is in the BloomFilter.

        Args:
            key (str): The key to test.

        Returns:
            bool: True if the key is in the BloomFilter, False otherwise.

        """
        bits_per_slice = self.bits_per_slice
        bitarray = self.bitarray
        hashes = self.make_hashes(key)
        offset = 0

        for k in hashes:
            if not bitarray[offset + k]:
                return False
            offset += bits_per_slice

        return True

    def __len__(self):
        """
        Return the number of keys stored by this bloom filter.

        Returns:
            int: Number of keys in the filter.

        """
        return self.count

    def add(self, key, skip_check=False):
        """
        Adds a key to the BloomFilter.

        Args:
            key (str): The key to add.
            skip_check (bool, optional): Whether to skip checking for existing keys.

        Returns:
            bool: True if the key was already in the BloomFilter, False otherwise.

        Raises:
            IndexError: If the BloomFilter is at capacity.

        """
        bitarray = self.bitarray
        bits_per_slice = self.bits_per_slice
        hashes = self.make_hashes(key)
        found_all_bits = True

        if self.count > self.capacity:
            raise IndexError("BloomFilter is at capacity")

        offset = 0
        for k in hashes:
            if not skip_check and found_all_bits and not bitarray[offset + k]:
                found_all_bits = False
            self.bitarray[offset + k] = True
            offset += bits_per_slice

        if skip_check:
            self.count += 1
            return False
        elif not found_all_bits:
            self.count += 1
            return False
        else:
            return True

    def copy(self):
        """
        Return a copy of this bloom filter.

        Returns:
            BloomFilter: A copy of the bloom filter.

        """
        new_filter = BloomFilter(self.capacity, self.error_rate)
        new_filter.bitarray = self.bitarray.copy()
        return new_filter

    def union(self, other):
        """
        Calculates the union of two BloomFilters and returns a new BloomFilter.

        Args:
            other (BloomFilter): Another BloomFilter.

        Returns:
            BloomFilter: A new BloomFilter representing the union.

        Raises:
            ValueError: If filters have different capacity or error rate.

        """
        if self.capacity != other.capacity or \
                        self.error_rate != other.error_rate:
            raise ValueError(
                "Unioning filters requires both filters to have both the same capacity and error rate")
        new_bloom = self.copy()
        new_bloom.bitarray = new_bloom.bitarray | other.bitarray
        return new_bloom

    def intersection(self, other):
        """
        Calculates the intersection of two BloomFilters and returns a new BloomFilter.

        Args:
            other (BloomFilter): Another BloomFilter.

        Returns:
            BloomFilter: A new BloomFilter representing the intersection.

        Raises:
            ValueError: If filters have different capacity or error rate.

        """
        if self.capacity != other.capacity or \
                        self.error_rate != other.error_rate:
            raise ValueError(
                "Intersecting filters requires both filters to have equal capacity and error rate")
        new_bloom = self.copy()
        new_bloom.bitarray = new_bloom.bitarray & other.bitarray
        return new_bloom

    def tofile(self, f):
        """
        Write the bloom filter to a file object.

        Args:
            f (file): The file object to write to.

        """
        f.write(pack(self.FILE_FMT, self.error_rate, self.num_slices,
                     self.bits_per_slice, self.capacity, self.count))
        (f.write(self.bitarray.tobytes()) if is_string_io(f)
         else self.bitarray.tofile(f))

    @classmethod
    def fromfile(cls, f, n=-1):
        """
        Read a bloom filter from a file-object.

        Args:
            f (file): The file object to read from.
            n (int, optional): Number of bytes to read.

        Returns:
            BloomFilter: A new BloomFilter.

        Raises:
            ValueError: If n is too small or if there's a bit length mismatch.

        """
        headerlen = calcsize(cls.FILE_FMT)

        if 0 < n < headerlen:
            raise ValueError('n too small!')

        filter = cls(1)  # Bogus instantiation, we will `_setup'.
        filter._setup(*unpack(cls.FILE_FMT, f.read(headerlen)))
        filter.bitarray = bitarray.bitarray(endian='little')
        if n > 0:
            (filter.bitarray.frombytes(f.read(n - headerlen)) if is_string_io(f)
             else filter.bitarray.fromfile(f, n - headerlen))
        else:
            (filter.bitarray.frombytes(f.read()) if is_string_io(f)
             else filter.bitarray.fromfile(f))
        if filter.num_bits != len(filter.bitarray) and \
                (filter.num_bits + (8 - filter.num_bits % 8) != len(filter.bitarray)):
            raise ValueError('Bit length mismatch!')

        return filter

    def __getstate__(self):
        """
        Return the state of the BloomFilter.

        Returns:
            dict: The state of the BloomFilter.

        """
        d = self.__dict__.copy()
        del d['make_hashes']
        return d

    def __setstate__(self, d):
        """
        Set the state of the BloomFilter.

        Args:
            d (dict): The state of the BloomFilter.

        """
        self.__dict__.update(d)
        self.make_hashes, self.hashfn = make_hashfuncs(self.num_slices, self.bits_per_slice)


class ScalableBloomFilter(object):
    """
    Implements a space-efficient probabilistic data structure that grows
    as more items are added while maintaining a steady false positive rate.

    Args:
        initial_capacity (int): The initial capacity of the filter.
        error_rate (float): The acceptable false positive error rate.
        mode (int): Growth mode (SMALL_SET_GROWTH or LARGE_SET_GROWTH).

    Attributes:
        SMALL_SET_GROWTH (int): Slower, but takes up less memory.
        LARGE_SET_GROWTH (int): Faster, but takes up more memory faster.
        FILE_FMT (bytes): Format for writing to a file.
        scale (int): Growth mode.
        ratio (float): Growth ratio.
        initial_capacity (int): Initial capacity of the filter.
        error_rate (float): False positive error rate.
        filters (list): List of underlying classic Bloom filters.

    """

    SMALL_SET_GROWTH = 2
    LARGE_SET_GROWTH = 4

    FILE_FMT = '<idQd'

    def __init__(self, initial_capacity=100, error_rate=0.001,
                 mode=LARGE_SET_GROWTH):
        """
        Initialize the ScalableBloomFilter.

        Args:
            initial_capacity (int, optional): The initial capacity of the filter.
            error_rate (float, optional): The acceptable false positive error rate.
            mode (int, optional): Growth mode (SMALL_SET_GROWTH or LARGE_SET_GROWTH).

        Raises:
            ValueError: If error_rate is invalid.

        """
        if not error_rate or error_rate < 0:
            raise ValueError("Error_Rate must be a decimal less than 0.")

        self._setup(mode, 0.9, initial_capacity, error_rate)
        self.filters = []

    def _setup(self, mode, ratio, initial_capacity, error_rate):
        """
        Set up the ScalableBloomFilter attributes.

        Args:
            mode (int): Growth mode.
            ratio (float): Growth ratio.
            initial_capacity (int): Initial capacity of the filter.
            error_rate (float): False positive error rate.

        """
        self.scale = mode
        self.ratio = ratio
        self.initial_capacity = initial_capacity
        self.error_rate = error_rate

    def __contains__(self, key):
        """
        Test if a key is in the ScalableBloomFilter.

        Args:
            key (str): The key to test.

        Returns:
            bool: True if the key is in the ScalableBloomFilter, False otherwise.

        """
        for f in reversed(self.filters):
            if key in f:
                return True
        return False

    def add(self, key):
        """
        Adds a key to the ScalableBloomFilter.

        Args:
            key (str): The key to add.

        Returns:
            bool: True if the key was already in the ScalableBloomFilter, False otherwise.

        """
        if key in self:
            return True

        if not self.filters:
            filter = BloomFilter(
                capacity=self.initial_capacity,
                error_rate=self.error_rate * self.ratio)
            self.filters.append(filter)
        else:
            filter = self.filters[-1]
            if filter.count >= filter.capacity:
                filter = BloomFilter(
                    capacity=filter.capacity * self.scale,
                    error_rate=filter.error_rate * self.ratio)
                self.filters.append(filter)

        filter.add(key, skip_check=True)
        return False

    def union(self, other):
        """
        Calculates the union of the underlying classic bloom filters and
        returns a new scalable bloom filter object.

        Args:
            other (ScalableBloomFilter): Another ScalableBloomFilter.

        Returns:
            ScalableBloomFilter: A new ScalableBloomFilter representing the union.

        Raises:
            ValueError: If filters have different mode, initial capacity, or error rate.

        """
        if self.scale != other.scale or \
                self.initial_capacity != other.initial_capacity or \
                self.error_rate != other.error_rate:
            raise ValueError("Unioning two scalable bloom filters requires \
            both filters to have both the same mode, initial capacity and error rate")

        if len(self.filters) > len(other.filters):
            larger_sbf = copy.deepcopy(self)
            smaller_sbf = other
        else:
            larger_sbf = copy.deepcopy(other)
            smaller_sbf = self

        # Union the underlying classic bloom filters
        new_filters = []
        for i in range(len(smaller_sbf.filters)):
            new_filter = larger_sbf.filters[i] | smaller_sbf.filters[i]
            new_filters.append(new_filter)

        for i in range(len(smaller_sbf.filters), len(larger_sbf.filters)):
            new_filters.append(larger_sbf.filters[i])

        larger_sbf.filters = new_filters
        return larger_sbf

    @property
    def capacity(self):
        """Returns the total capacity for all filters in this SBF"""
        return sum(f.capacity for f in self.filters)

    @property
    def count(self):
        """
        Returns the total number of elements stored in this SBF.

        Returns:
            int: Total number of elements stored.

        """
        return len(self)

    def tofile(self, f):
        """
        Serialize this ScalableBloomFilter into the file-object `f'.

        Args:
            f (file): The file object to write to.

        """
        f.write(pack(self.FILE_FMT, self.scale, self.ratio,
                     self.initial_capacity, self.error_rate))

        # Write #-of-filters
        f.write(pack(b'<l', len(self.filters)))

        if len(self.filters) > 0:
            # Then each filter directly, with a header describing
            # their lengths.
            headerpos = f.tell()
            headerfmt = b'<' + b'Q' * (len(self.filters))
            f.write(b'.' * calcsize(headerfmt))
            filter_sizes = []

            for filter in self.filters:
                begin = f.tell()
                filter.tofile(f)
                filter_sizes.append(f.tell() - begin)

            f.seek(headerpos)
            f.write(pack(headerfmt, *filter_sizes))

    @classmethod
    def fromfile(cls, f):
        """
        Deserialize the ScalableBloomFilter in file object `f'.

        Args:
            f (file): The file object to read from.

        Returns:
            ScalableBloomFilter: A new ScalableBloomFilter.

        """
        filter = cls()
        filter._setup(*unpack(cls.FILE_FMT, f.read(calcsize(cls.FILE_FMT))))
        nfilters, = unpack(b'<l', f.read(calcsize(b'<l')))

        if nfilters > 0:
            header_fmt = b'<' + b'Q' * nfilters
            bytes = f.read(calcsize(header_fmt))
            filter_lengths = unpack(header_fmt, bytes)

            for fl in filter_lengths:
                filter.filters.append(BloomFilter.fromfile(f, fl))
        else:
            filter.filters = []

        return filter

    def __len__(self):
        """
        Returns the total number of elements stored in this SBF.

        Returns:
            int: Total number of elements stored.

        """
        return sum(f.count for f in self.filters)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
