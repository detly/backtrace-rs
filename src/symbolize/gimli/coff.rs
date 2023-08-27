use super::{gimli, Context, Endian, EndianSlice, Mapping, Path, Stash, Vec};
use alloc::sync::Arc;
use core::convert::TryFrom;
use object::pe::{ImageDosHeader, ImageSymbol};
use object::read::coff::ImageSymbol as _;
use object::read::pe::{ImageNtHeaders, ImageOptionalHeader, SectionTable};
use object::read::StringTable;
use object::LittleEndian as LE;

#[cfg(target_pointer_width = "32")]
type Pe = object::pe::ImageNtHeaders32;
#[cfg(target_pointer_width = "64")]
type Pe = object::pe::ImageNtHeaders64;

impl Mapping {
    pub fn new(path: &Path) -> Option<Mapping> {
        let map = super::mmap(path)?;
        Mapping::mk(map, |data, stash| {
            Context::new(stash, Object::parse(data)?, None, None)
        })
    }
}

pub struct Object<'a> {
    data: &'a [u8],
    sections: SectionTable<'a>,
    symbols: Vec<(usize, &'a ImageSymbol)>,
    strings: StringTable<'a>,
}

pub fn get_image_base(data: &[u8]) -> Option<usize> {
    let dos_header = ImageDosHeader::parse(data).ok()?;
    let mut offset = dos_header.nt_headers_offset().into();
    let (nt_headers, _) = Pe::parse(data, &mut offset).ok()?;
    usize::try_from(nt_headers.optional_header().image_base()).ok()
}

impl<'a> Object<'a> {
    fn parse(data: &'a [u8]) -> Option<Object<'a>> {
        None
    }

    pub fn section(&self, _: &Stash, name: &str) -> Option<&'a [u8]> {
        None
    }

    pub fn search_symtab<'b>(&'b self, addr: u64) -> Option<&'b [u8]> {
        None
    }

    pub(super) fn search_object_map(&self, _addr: u64) -> Option<(&Context<'_>, u64)> {
        None
    }
}

pub(super) fn handle_split_dwarf<'data>(
    _package: Option<&gimli::DwarfPackage<EndianSlice<'data, Endian>>>,
    _stash: &'data Stash,
    _load: addr2line::SplitDwarfLoad<EndianSlice<'data, Endian>>,
) -> Option<Arc<gimli::Dwarf<EndianSlice<'data, Endian>>>> {
    None
}
